import os
from pathlib import Path
from tempfile import TemporaryDirectory

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from shapeworks_cloud.core import models
from swcc.api import swcc_session
from swcc.models import Project as SWCCProject

from .tasks import edit_swproj_section


def run_prep(params, project, project_file, progress):
    import DeepSSMUtils
    import shapeworks as sw

    # //////////////////////////////////////////////
    # /// STEP 1: Create Split
    # //////////////////////////////////////////////
    val_split = float(params['validation_split'])
    test_split = float(params['testing_split'])

    train_split = 100.0 - val_split - test_split
    DeepSSMUtils.create_split(project, train_split, val_split, test_split)

    # /////////////////////////////////////////////////////////////////
    # /// STEP 2: Groom Training Shapes
    # /////////////////////////////////////////////////////////////////
    progress.update_message('Grooming Training Shapes...')

    project_params = project.get_parameters('groom')
    # alignment should always be set to ICP
    project_params.set('alignment_method', 'Iterative Closest Point')
    project_params.set('alignment_enabled', 'true')
    project.set_parameters('groom', project_params)

    DeepSSMUtils.groom_training_shapes(project)
    project.save(project_file)

    progress.update_percentage(11)

    # /////////////////////////////////////////////////////////////////
    # /// STEP 3: Optimize Training Particles
    # /////////////////////////////////////////////////////////////////
    progress.update_message('Optimizing Training Particles...')
    DeepSSMUtils.optimize_training_particles(project)
    project.save(project_file)
    progress.update_percentage(12)

    # /////////////////////////////////////////////////////////////////
    # /// STEP 4: Groom Training Images
    # /////////////////////////////////////////////////////////////////
    progress.update_message('Grooming Training Images...')
    DeepSSMUtils.groom_training_images(project)
    project.save(project_file)

    # /////////////////////////////////////////////////////////////////
    # /// STEP 5: Groom Validation Images
    # /////////////////////////////////////////////////////////////////
    progress.update_message('Grooming Validation Images...')
    val_indices = DeepSSMUtils.get_split_indices(project, 'val')
    test_indices = DeepSSMUtils.get_split_indices(project, 'test')
    val_test_indices = val_indices + test_indices
    DeepSSMUtils.groom_val_test_images(project, val_test_indices)
    project.save(project_file)
    progress.update_percentage(14)

    # /////////////////////////////////////////////////////////////////
    # /// STEP 6: Optimize Validation Particles with Fixed Domains
    # /////////////////////////////////////////////////////////////////
    DeepSSMUtils.prep_project_for_val_particles(project)

    project_params = project.get_parameters('optimize')
    project_params.set('multiscale', '0')
    project_params.set('procrustes', '0')
    project_params.set('procrustes_interval', '0')
    project_params.set('procrustes_scaling', '0')
    project_params.set('narrow_band', '1e10')

    project.set_parameters('optimize', project_params)

    progress.update_message('Grooming Validation Shapes...')
    DeepSSMUtils.groom_validation_shapes(project)
    project.save(project_file)
    progress.update_percentage(17)

    progress.update_message('Optimizing Validation Particles...')
    optimize = sw.Optimize()
    optimize.SetUpOptimize(project)
    optimize.Run()

    project.save(project_file)
    progress.update_percentage(20)


def run_augmentation(params, project, download_dir, progress):
    import DataAugmentationUtils
    import DeepSSMUtils

    # /////////////////////////////////////////////////////////////////
    # /// STEP 7: Augment Data
    # /////////////////////////////////////////////////////////////////
    num_samples = int(params['aug_num_samples'])
    percent_variability = float(params['percent_variability'])
    aug_sampler_type = params['aug_sampler_type'].lower()

    num_dims = 0  # set to 0 to allow for percent variability to be used

    progress.update_message('Running Data Augmentation...')
    embedded_dims = DeepSSMUtils.run_data_augmentation(
        project,
        num_samples,
        num_dims,
        percent_variability,
        aug_sampler_type,
        mixture_num=0,
        processes=1,  # Thread count
    )
    progress.update_message('Generating Augmentation visualizations...')
    progress.update_percentage(25)

    aug_dir = download_dir + '/deepssm/augmentation/'
    aug_data_csv = aug_dir + 'TotalData.csv'

    DataAugmentationUtils.visualizeAugmentation(aug_data_csv, 'violin')
    progress.update_percentage(30)

    return embedded_dims


def run_training(params, project, download_dir, aug_dims, progress):
    import DeepSSMUtils

    batch_size = int(params['train_batch_size'])

    # /////////////////////////////////////////////////////////////////
    # /// STEP 8: Create PyTorch loaders from data
    # /////////////////////////////////////////////////////////////////
    progress.update_message('Preparing Training Data Loaders...')
    DeepSSMUtils.prepare_data_loaders(project, batch_size, 'train')
    DeepSSMUtils.prepare_data_loaders(project, batch_size, 'val')
    progress.update_percentage(35)

    # /////////////////////////////////////////////////////////////////
    # /// STEP 9: Train DeepSSM Model
    # /////////////////////////////////////////////////////////////////
    out_dir = download_dir + '/deepssm/'
    aug_dir = out_dir + 'augmentation/'

    loader_dir = out_dir + 'torch_loaders/'

    epochs = int(params['train_epochs'])
    learning_rate = float(params['train_learning_rate'])
    decay_learning_rate = params['train_decay_learning_rate']
    fine_tune = params['train_fine_tuning']
    fine_tune_epochs = int(params['train_fine_tuning_epochs'])
    fine_tune_learning_rate = float(params['train_fine_tuning_learning_rate'])
    loss_function = params['train_loss_function']

    config_file = out_dir + 'configuration.json'

    DeepSSMUtils.prepare_config_file(
        config_file,
        'model',
        aug_dims,
        out_dir,
        loader_dir,
        aug_dir,
        epochs,
        learning_rate,
        decay_learning_rate,
        fine_tune,
        fine_tune_epochs,
        fine_tune_learning_rate,
        loss_function,
    )
    progress.update_percentage(40)

    progress.update_message('Training DeepSSM Model...')
    DeepSSMUtils.trainDeepSSM(project, config_file)
    progress.update_percentage(50)


def run_testing(params, project, download_dir, progress):
    import DeepSSMUtils

    test_indices = DeepSSMUtils.get_split_indices(project, 'test')

    # /////////////////////////////////////////////////////////////////
    # /// STEP 10: Groom Testing Images
    # /////////////////////////////////////////////////////////////////
    progress.update_message('Grooming Testing Images...')
    DeepSSMUtils.groom_val_test_images(project, test_indices)
    progress.update_percentage(55)

    # /////////////////////////////////////////////////////////////////
    # /// STEP 11: Prepare Test Data PyTorch Loaders
    # /////////////////////////////////////////////////////////////////
    progress.update_message('Preparing Testing Data Loaders...')
    batch_size = int(params['train_batch_size'])
    DeepSSMUtils.prepare_data_loaders(project, batch_size, 'test')

    test_names_file = download_dir + '/deepssm/torch_loaders/test_names.txt'

    with open(test_names_file, 'w') as file:
        list_items = ["'" + str(id) + "'" for id in test_indices]
        file.write('[')
        file.write(', '.join(list_items))
        file.write(']')

    config_file = download_dir + '/deepssm/configuration.json'
    progress.update_percentage(60)

    # /////////////////////////////////////////////////////////////////
    # /// STEP 12: Test DeepSSM Model
    # /////////////////////////////////////////////////////////////////
    progress.update_message('Testing DeepSSM Model...')
    DeepSSMUtils.testDeepSSM(config_file)
    
    progress.update_messsage('Processing Test Predictions...')
    progress.update_percentage(75)
    DeepSSMUtils.process_test_predictions(project, config_file)
    progress.update_percentage(90)


def run_deepssm_command(
    user_id,
    project_id,
    form_data,
    command,
    pre_command_function,
    post_command_function,
    progress_id,
):
    import shapeworks as sw

    user = User.objects.get(id=user_id)
    progress = models.TaskProgress.objects.get(id=progress_id)
    token, _created = Token.objects.get_or_create(user=user)
    base_url = settings.API_URL  # type: ignore

    try:
        with TemporaryDirectory() as download_dir:
            with swcc_session(base_url=base_url) as session:
                # fetch everything we need
                progress.update_message('Downloading Project...')
                session.set_token(token.key)
                project = models.Project.objects.get(id=project_id)
                project_filename = project.file.name.split('/')[-1]
                swcc_project = SWCCProject.from_id(project.id)
                swcc_project.download(download_dir)

                pre_command_function()
                progress.update_percentage(10)
                progress.update_message('Running DeepSSM Command...')

                if form_data:
                    # write the form data to the project file
                    edit_swproj_section(
                        Path(download_dir, project_filename),
                        'deepssm',
                        form_data,
                    )

                result_data = {}

                # Use shapeworks python project class
                sw_project = sw.Project()

                sw_project_file = str(Path(download_dir, project_filename))

                sw_project.load(sw_project_file)

                groom_params = sw_project.get_parameters('groom')

                # for each parameter in the form data, set the parameter in the project
                for key, value in form_data.items():
                    groom_params.set(key, value)

                sw_project.set_parameters('groom', groom_params)

                optimize_params = sw_project.get_parameters('optimize')
                # for each parameter in the form data, set the parameter in the project
                for key, value in form_data.items():
                    optimize_params.set(key, value)

                sw_project.set_parameters('optimize', optimize_params)

                os.chdir(sw_project.get_project_path())
                run_prep(form_data, sw_project, sw_project_file, progress)

                aug_dims = run_augmentation(form_data, sw_project, download_dir, progress)

                # result data has paths to files
                result_data['augmentation'] = {
                    'total_data_csv': download_dir + '/deepssm/augmentation/TotalData.csv',
                    'violin_plot': download_dir + '/deepssm/augmentation/violin.png',
                    'generated_meshes': os.listdir(
                        download_dir + '/deepssm/augmentation/Generated-Meshes/'
                    ),
                    'generated_images': os.listdir(
                        download_dir + '/deepssm/augmentation/Generated-Images/'
                    ),
                    'generated_particles': os.listdir(
                        download_dir + '/deepssm/augmentation/Generated-Particles/'
                    ),
                }

                run_training(form_data, sw_project, download_dir, aug_dims, progress)

                training_examples = os.listdir(download_dir + '/deepssm/model/examples/')

                if 'train_' in training_examples:
                    training_examples.remove('train_')
                if 'validation_' in training_examples:
                    training_examples.remove('validation_')

                result_data['training'] = {
                    'train_log': download_dir + '/deepssm/model/train_log.csv',
                    'training_plot': download_dir + '/deepssm/model/training_plot.png',
                    'training_plot_ft': download_dir + '/deepssm/model/training_plot_ft.png',
                    'train_examples': training_examples,
                    'train_images': os.listdir(download_dir + '/deepssm/train_images/'),
                    'val_and_test_images': os.listdir(
                        download_dir + '/deepssm/val_and_test_images/'
                    ),
                }

                run_testing(form_data, sw_project, download_dir, progress)
                progress.update_message("Saving Results...")

                subjects = sw_project.get_subjects()

                result_data['testing'] = {
                    'world_predictions': os.listdir(
                        download_dir + '/deepssm/model/test_predictions/world_predictions/'
                    ),
                    'local_predictions': os.listdir(
                        download_dir + '/deepssm/model/test_predictions/local_predictions/'
                    ),
                    'test_distances': download_dir + '/deepssm/test_distances.csv',
                    'test_split_subjects': subjects,
                }

                os.chdir('../../')

                post_command_function(project, download_dir, result_data, project_filename)
                progress.update_percentage(100)
    except models.TaskProgress.TaskAbortedError:
        print('Task Aborted. Exiting.')
    except Exception as e:
        progress.update_error(str(e))


@shared_task
def deepssm_run(user_id, project_id, progress_id, form_data):
    def pre_command_function():
        project = models.Project.objects.get(id=project_id)

        # delete any previous results.
        models.DeepSSMResult.objects.filter(project=project).delete()
        models.DeepSSMAugPair.objects.filter(project=project).delete()
        models.DeepSSMTrainingPair.objects.filter(project=project).delete()
        models.DeepSSMTrainingImage.objects.filter(project=project).delete()
        models.DeepSSMTestingData.objects.filter(project=project).delete()

    def post_command_function(project, download_dir, result_data, project_filename):
        # save project file changes to database
        project.file.save(
            project_filename,
            open(Path(download_dir, project_filename), 'rb'),
        )

        deepssm_result = models.DeepSSMResult.objects.create(
            project=project,
        )

        # augmentation
        deepssm_result.aug_visualization.save(
            'violin_plot.png',
            open(result_data['augmentation']['violin_plot'], 'rb'),
        )

        deepssm_result.aug_total_data.save(
            'TotalData.csv',
            open(result_data['augmentation']['total_data_csv'], 'rb'),
        )

        # create aug pairs
        for i in range(0, len(result_data['augmentation']['generated_images'])):
            aug_pair = models.DeepSSMAugPair.objects.create(
                project=project,
                sample_num=int(  # get sample number from filename
                    result_data['augmentation']['generated_images'][i].split('_')[2].split('.')[0],
                ),
            )
            aug_pair.mesh.save(
                result_data['augmentation']['generated_meshes'][i],
                open(
                    download_dir
                    + '/deepssm/augmentation/Generated-Meshes/'
                    + result_data['augmentation']['generated_meshes'][i],
                    'rb',
                ),
            )
            aug_pair.image.save(
                result_data['augmentation']['generated_images'][i],
                open(
                    download_dir
                    + '/deepssm/augmentation/Generated-Images/'
                    + result_data['augmentation']['generated_images'][i],
                    'rb',
                ),
            )
            aug_pair.particles.save(
                result_data['augmentation']['generated_particles'][i],
                open(
                    download_dir
                    + '/deepssm/augmentation/Generated-Particles/'
                    + result_data['augmentation']['generated_particles'][i],
                    'rb',
                ),
            )

        # training
        deepssm_result.training_visualization.save(
            'training_plot.png',
            open(result_data['training']['training_plot'], 'rb'),
        )
        deepssm_result.training_visualization_ft.save(
            'training_plot_ft.png',
            open(result_data['training']['training_plot_ft'], 'rb'),
        )
        deepssm_result.training_data_table.save(
            'train_log.csv',
            open(result_data['training']['train_log'], 'rb'),
        )

        # testing
        deepssm_result.testing_distances.save(
            'test_distances.csv',
            open(result_data['testing']['test_distances'], 'rb'),
        )

        world_predictions = result_data['testing']['world_predictions']
        local_predictions = result_data['testing']['local_predictions']

        # create test pairs
        for predictions in [world_predictions, local_predictions]:
            for _i in range(0, len(predictions)):
                if len(predictions) > 0:
                    # in world_predictions, there's two files with the same name,
                    # but .vtk and .particles file types. Add these to mesh and partciles field
                    file1 = predictions.pop()
                    filename = file1.split('.')[0]

                    # filename here represents the SUBJECT INDEX OF THE TEST SPLIT
                    subject_name = result_data['testing']['test_split_subjects'][
                        int(filename)
                    ].get_display_name()

                    test_pair = models.DeepSSMTestingData.objects.create(
                        project=project,
                        image_type='world' if predictions == world_predictions else 'local',
                        image_id=subject_name,
                    )

                    predictions_path = (
                        download_dir
                        + '/deepssm/model/test_predictions/'
                        + (
                            'world_predictions/'
                            if predictions == world_predictions
                            else 'local_predictions/'
                        )
                    )

                    if file1.split('.')[1] == 'vtk':
                        file2 = predictions.pop(predictions.index(filename + '.particles'))
                        test_pair.mesh.save(
                            file1,
                            open(
                                predictions_path + file1,
                                'rb',
                            ),
                        )
                        test_pair.particles.save(
                            file2,
                            open(
                                predictions_path + file2,
                                'rb',
                            ),
                        )
                    else:
                        file2 = predictions.pop(predictions.index(filename + '.vtk'))
                        test_pair.mesh.save(
                            file2,
                            open(
                                predictions_path + file2,
                                'rb',
                            ),
                        )
                        test_pair.particles.save(
                            file1,
                            open(
                                predictions_path + file1,
                                'rb',
                            ),
                        )

        train_images = result_data['training']['train_images']
        val_and_test_images = result_data['training']['val_and_test_images']
        # create training images
        for images in [train_images, val_and_test_images]:
            for image in images:
                image_type = 'train' if images == train_images else 'val_and_test'

                train_image = models.DeepSSMTrainingImage.objects.create(
                    project=project,
                    validation=True if image_type == 'val_and_test' else False,
                    index=image.split('.')[0],
                )
                train_image.image.save(
                    image,
                    open(
                        download_dir + '/deepssm/' + image_type + '_images/' + image,
                        'rb',
                    ),
                )

        examples = result_data['training']['train_examples']

        # get all values of examples that have "training" or "validation" in the name
        training_examples = [example for example in examples if 'train' in example]
        validation_examples = [example for example in examples if 'validation' in example]

        for example_group in [training_examples, validation_examples]:
            # get all values in the example_group which have "worst", then "median", then "best"
            worst = [example for example in example_group if 'worst' in example]
            median = [example for example in example_group if 'median' in example]
            best = [example for example in example_group if 'best' in example]

            for group_type in [worst, median, best]:
                # get each file type from group list (should only be 1 of each)
                particles_file = next(filter(lambda x: 'particles' in x, group_type))
                scalars_file = next(filter(lambda x: 'scalars' in x, group_type))
                vtk_file = next(filter(lambda x: 'vtk' in x, group_type))
                index_file = next(filter(lambda x: 'index' in x, group_type))

                training_pair = models.DeepSSMTrainingPair.objects.create(
                    project=project,
                    validation=True if example_group == validation_examples else False,
                    example_type=(
                        'best'
                        if group_type == best
                        else 'median' if group_type == median else 'worst'
                    ),
                )

                training_pair.particles.save(
                    particles_file,
                    open(
                        download_dir + '/deepssm/model/examples/' + particles_file,
                        'rb',
                    ),
                )

                training_pair.scalar.save(
                    scalars_file,
                    open(
                        download_dir + '/deepssm/model/examples/' + scalars_file,
                        'rb',
                    ),
                )

                training_pair.mesh.save(
                    vtk_file,
                    open(
                        download_dir + '/deepssm/model/examples/' + vtk_file,
                        'rb',
                    ),
                )

                # read index file and save the contents to the index field
                with open(download_dir + '/deepssm/model/examples/' + index_file, 'r') as file:
                    training_pair.index = file.read()
                    training_pair.save()

    run_deepssm_command(
        user_id,
        project_id,
        form_data,
        'deepssm',
        pre_command_function,
        post_command_function,
        progress_id,
    )
