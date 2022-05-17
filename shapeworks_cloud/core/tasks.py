from pathlib import Path
from subprocess import PIPE, Popen
from tempfile import TemporaryDirectory

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
import openpyxl
import pandas
from rest_framework.authtoken.models import Token

from shapeworks_cloud.core.models import (
    GroomedMesh,
    GroomedSegmentation,
    Mesh,
    Project,
    Segmentation,
)
from swcc.api import swcc_session
from swcc.models import Dataset as SWCCDataset


def edit_excel_tab(filename, tab_name, new_df):
    book = openpyxl.load_workbook(filename)
    # delete old version of that sheet
    if 'groom' in book.sheetnames:
        book.remove_sheet(book.get_sheet_by_name(tab_name))

    writer = pandas.ExcelWriter(filename, engine='openpyxl')
    writer.book = book
    writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
    new_df.to_excel(writer, tab_name, index=False)
    writer.save()


def interpret_groom_form_df(df):
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


@shared_task
def groom(user_id, project_id, form_data):
    user = User.objects.get(id=user_id)
    token, _created = Token.objects.get_or_create(user=user)
    base_url = settings.API_URL

    with TemporaryDirectory() as download_dir:
        with swcc_session(base_url=base_url) as session:
            # fetch everything we need
            session.set_token(token.key)
            project = Project.objects.get(id=project_id)
            project_filename = project.file.name.split('/')[-1]
            dataset = SWCCDataset.from_id(project.dataset.id)
            dataset.download(download_dir)

            # delete any previous results
            GroomedSegmentation.objects.filter(project=project.id).delete()
            GroomedMesh.objects.filter(project=project.id).delete()

            # write the form data to the project spreadsheet
            form_df = pandas.DataFrame(
                list(form_data.items()),
                columns=['key', 'value'],
            )
            form_df = interpret_groom_form_df(form_df)
            edit_excel_tab(
                Path(download_dir, project_filename),
                'groom',
                form_df,
            )

            # perform groom
            process = Popen(
                [
                    '/opt/shapeworks/bin/shapeworks',
                    'groom',
                    f'--name={project_filename}',
                ],
                cwd=download_dir,
                stdout=PIPE,
                stderr=PIPE,
            )
            _out, _err = process.communicate()

            # read the changed project excel file for resulting files
            new_project_df = pandas.read_excel(
                Path(download_dir, project_filename), sheet_name='data'
            )
            project_segmentations = Segmentation.objects.filter(
                subject__dataset__id=project.dataset.id
            )
            project_meshes = Mesh.objects.filter(subject__dataset__id=project.dataset.id)
            for _, row in new_project_df.iterrows():
                source_filename = row['shape_1'].split('/')[-1]
                result_file = Path(download_dir, row['groomed_1'])
                target_object = project_segmentations.get(
                    file__endswith=source_filename,
                )
                if not target_object:
                    project_meshes.get(
                        file__endswith=source_filename,
                    )
                    result_object = GroomedMesh.objects.create(
                        project=project,
                        mesh=target_object,
                    )
                else:
                    result_object = GroomedSegmentation.objects.create(
                        project=project,
                        segmentation=target_object,
                    )
                result_object.file.save(
                    row['groomed_1'],
                    open(result_file, 'rb'),
                )
