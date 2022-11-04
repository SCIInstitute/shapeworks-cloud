import json
from pathlib import Path
from subprocess import PIPE, Popen
from tempfile import TemporaryDirectory

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
import pandas
from rest_framework.authtoken.models import Token

from shapeworks_cloud.core import models
from swcc.api import swcc_session
from swcc.models import Project as SWCCProject


def edit_swproj_section(filename, section_name, new_df):
    with open(filename, 'r') as f:
        data = json.load(f)
    new_contents = {item['key']: item['value'] for item in new_df.to_dict(orient='records')}
    if section_name == 'groom':
        data[section_name] = {}
        data[section_name]['shape'] = new_contents
    else:
        data[section_name] = new_contents
    with open(filename, 'w') as f:
        json.dump(data, f)


def interpret_form_df(df, command):
    if command == 'groom' and df['key'].str.contains('anisotropic_').any():
        # consolidate anisotropic values to one row
        anisotropic_values = {
            axis: str(df.loc[df['key'] == 'anisotropic_' + axis].iloc[0]['value'])
            for axis in ['x', 'y', 'z']
        }
        df_filter = df['key'].map(lambda key: 'anisotropic_' not in key)
        df = df[df_filter]
        return pandas.concat(
            [
                df,
                pandas.DataFrame.from_dict(
                    {
                        'key': ['spacing'],
                        'value': [' '.join(anisotropic_values.values())],
                    }
                ),
            ]
        )
    else:
        return df


def run_shapeworks_command(
    user_id,
    project_id,
    form_data,
    command,
    pre_command_function,
    post_command_function,
):
    user = User.objects.get(id=user_id)
    token, _created = Token.objects.get_or_create(user=user)
    base_url = settings.API_URL

    with TemporaryDirectory() as download_dir:
        with swcc_session(base_url=base_url) as session:
            # fetch everything we need
            session.set_token(token.key)
            project = models.Project.objects.get(id=project_id)
            project_filename = project.file.name.split('/')[-1]
            SWCCProject.from_id(project.id).download(download_dir)

            pre_command_function()

            # write the form data to the project file
            form_df = pandas.DataFrame(
                list(form_data.items()),
                columns=['key', 'value'],
            )
            form_df = interpret_form_df(form_df, command)
            edit_swproj_section(
                Path(download_dir, project_filename),
                command,
                form_df,
            )

            # perform command
            process = Popen(
                [
                    '/opt/shapeworks/bin/shapeworks',
                    command,
                    f'--name={project_filename}',
                ],
                cwd=download_dir,
                stdout=PIPE,
                stderr=PIPE,
            )
            _out, _err = process.communicate()
            # TODO: raise _err to user if not empty
            print(_out, _err)

            with open(Path(download_dir, project_filename), 'r') as f:
                project_data = json.load(f)
            post_command_function(project, download_dir, project_data, project_filename)


@shared_task
def groom(user_id, project_id, form_data):
    def pre_command_function():
        # delete any previous results
        models.GroomedSegmentation.objects.filter(project=project_id).delete()
        models.GroomedMesh.objects.filter(project=project_id).delete()

    def post_command_function(project, download_dir, project_data, project_filename):
        # save project file changes to database
        project.file.save(
            project_filename,
            open(Path(download_dir, project_filename), 'rb'),
        )

        # make new objects in database
        project_segmentations = models.Segmentation.objects.filter(
            subject__dataset__id=project.dataset.id
        )
        project_meshes = models.Mesh.objects.filter(subject__dataset__id=project.dataset.id)
        for row in project_data['data']:
            source_filename = row['shape_1'].split('/')[-1]
            result_file = Path(download_dir, row['groomed_1'])
            try:
                target_object = project_segmentations.get(
                    file__endswith=source_filename,
                )
                result_object = models.GroomedSegmentation.objects.create(
                    project=project,
                    segmentation=target_object,
                )
            except models.Segmentation.DoesNotExist:
                target_object = project_meshes.get(
                    file__endswith=source_filename,
                )
                result_object = models.GroomedMesh.objects.create(
                    project=project,
                    mesh=target_object,
                )
            result_object.file.save(
                row['groomed_1'],
                open(result_file, 'rb'),
            )

    run_shapeworks_command(
        user_id, project_id, form_data, 'groom', pre_command_function, post_command_function
    )


@shared_task
def optimize(user_id, project_id, form_data):
    def pre_command_function():
        # delete any previous results
        models.OptimizedParticles.objects.filter(project=project_id).delete()

    def post_command_function(project, download_dir, project_data, project_filename):
        # save project file changes to database
        project.file.save(
            project_filename,
            open(Path(download_dir, project_filename), 'rb'),
        )

        # make new objects in database
        project_groomed_segmentations = models.GroomedSegmentation.objects.filter(project=project)
        project_groomed_meshes = models.GroomedMesh.objects.filter(project=project)
        for row in project_data['data']:
            groomed_filename = row['groomed_1'].split('/')[-1]
            target_segmentation = project_groomed_segmentations.filter(
                file__endswith=groomed_filename,
            ).first()
            target_mesh = project_groomed_meshes.filter(
                file__endswith=groomed_filename,
            ).first()
            result_particles_object = models.OptimizedParticles.objects.create(
                groomed_segmentation=target_segmentation,
                groomed_mesh=target_mesh,
                project=project,
            )
            result_particles_object.world.save(
                row['world_particles_1'].split('/')[-1],
                open(Path(download_dir, row['world_particles_1']), 'rb'),
            )
            result_particles_object.local.save(
                row['local_particles_1'].split('/')[-1],
                open(Path(download_dir, row['local_particles_1']), 'rb'),
            )
            result_particles_object.transform.save(
                '.'.join(row['shape_1'].split('/')[-1].split('.')[:-1]) + '.transform',
                ContentFile(str(row['alignment_1']).encode()),
            )

    run_shapeworks_command(
        user_id, project_id, form_data, 'optimize', pre_command_function, post_command_function
    )
