from pathlib import Path
from subprocess import PIPE, Popen
from tempfile import TemporaryDirectory

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
import openpyxl
import pandas
from rest_framework.authtoken.models import Token

from shapeworks_cloud.core import models
from swcc.api import swcc_session
from swcc.models import Dataset as SWCCDataset


def edit_excel_tab(filename, tab_name, new_df):
    book = openpyxl.load_workbook(filename)
    # delete old version of that sheet
    if tab_name in book.sheetnames:
        book.remove_sheet(book.get_sheet_by_name(tab_name))

    writer = pandas.ExcelWriter(filename, engine='openpyxl')
    writer.book = book
    writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
    new_df.to_excel(writer, tab_name, index=False)
    writer.save()


def interpret_form_df(df, command):
    if command == 'groom':
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
            dataset = SWCCDataset.from_id(project.dataset.id)
            dataset.download(download_dir)

            pre_command_function()

            # write the form data to the project spreadsheet
            form_df = pandas.DataFrame(
                list(form_data.items()),
                columns=['key', 'value'],
            )
            form_df = interpret_form_df(form_df, command)
            edit_excel_tab(
                Path(download_dir, project_filename),
                command,
                form_df,
            )
            project_dfs = pandas.read_excel(Path(download_dir, project_filename), sheet_name=None)

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

            post_command_function(project, download_dir, project_dfs, project_filename)


def save_dfs_to_project_spreadsheet(
    project,
    download_dir,
    project_dfs,
    project_filename,
    update_columns={},
):
    for sheet_name, columns in update_columns.items():
        for column_name in columns:
            # update project_dfs according to change after operation
            project_dfs[sheet_name][column_name] = pandas.read_excel(
                Path(download_dir, project_filename), sheet_name=sheet_name
            )[column_name]

    new_project_file = Path(download_dir, 'new_project_data.xlsx')
    with pandas.ExcelWriter(new_project_file) as writer:
        [
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
            for sheet_name, sheet_df in project_dfs.items()
        ]

    # save project file changes to database
    project.file.save(
        project_filename,
        open(new_project_file, 'rb'),
    )


@shared_task
def groom(user_id, project_id, form_data):
    def pre_command_function():
        # delete any previous results
        models.GroomedSegmentation.objects.filter(project=project_id).delete()
        models.GroomedMesh.objects.filter(project=project_id).delete()

    def post_command_function(project, download_dir, project_dfs, project_filename):
        save_dfs_to_project_spreadsheet(
            project,
            download_dir,
            project_dfs,
            project_filename,
            update_columns={'data': ['groomed_1']},
        )

        # make new objects in database
        project_segmentations = models.Segmentation.objects.filter(
            subject__dataset__id=project.dataset.id
        )
        project_meshes = models.Mesh.objects.filter(subject__dataset__id=project.dataset.id)
        for _, row in project_dfs['data'].iterrows():
            source_filename = row['shape_1'].split('/')[-1]
            result_file = Path(download_dir, row['groomed_1'])
            target_object = project_segmentations.get(
                file__endswith=source_filename,
            )
            if not target_object:
                project_meshes.get(
                    file__endswith=source_filename,
                )
                result_object = models.GroomedMesh.objects.create(
                    project=project,
                    mesh=target_object,
                )
            else:
                result_object = models.GroomedSegmentation.objects.create(
                    project=project,
                    segmentation=target_object,
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
        models.OptimizedShapeModel.objects.filter(project=project_id).delete()

    def post_command_function(project, download_dir, project_dfs, project_filename):
        save_dfs_to_project_spreadsheet(
            project,
            download_dir,
            project_dfs,
            project_filename,
            update_columns={'data': ['alignment_1', 'local_particles_1', 'world_particles_1']},
        )

        # make new objects in database
        project_groomed_segmentations = models.GroomedSegmentation.objects.filter(project=project)
        project_groomed_meshes = models.GroomedMesh.objects.filter(project=project)
        for _, row in project_dfs['data'].iterrows():
            groomed_filename = row['groomed_1'].split('/')[-1]
            target_segmentation = project_groomed_segmentations.filter(
                file__endswith=groomed_filename,
            ).first()
            target_mesh = project_groomed_meshes.filter(
                file__endswith=groomed_filename,
            ).first()
            result_shape_object = models.OptimizedShapeModel.objects.create(
                project=project, parameters=form_data
            )
            result_particles_object = models.OptimizedParticles.objects.create(
                groomed_segmentation=target_segmentation,
                groomed_mesh=target_mesh,
                shape_model=result_shape_object,
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
