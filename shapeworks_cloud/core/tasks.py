from pathlib import Path
from subprocess import Popen, PIPE
from tempfile import TemporaryDirectory

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from swcc.api import swcc_session
from swcc.models import Dataset, Project

# TODO generate an empty project if necessary so that a fresh dataset can be groomed
# The groom command needs a project spreadsheet to run
# @shared_task
# def groom_dataset(user_id, dataset_id):
#     ...


@shared_task
def groom(user_id, project_id):
    user = User.objects.get(id=user_id)
    token, _created = Token.objects.get_or_create(user=user)
    base_url = settings.API_URL
    with TemporaryDirectory() as download_dir:
        with swcc_session(base_url=base_url) as session:
            session.set_token(token.key)
            project = Project.from_id(project_id)
            dataset = project.dataset
            dataset.download(download_dir)
            process = Popen(
                ['/opt/shapeworks/bin/shapeworks', 'groom', f'--name={project.file.name}'],
                cwd=download_dir,
                stdout=PIPE,
                stderr=PIPE,
            )
            _out, _err = process.communicate()
            # TODO raise an error to the user when the executable fails

            # TODO Determine correct behavior for deleting old groomed data
            # For now, just delete the whole project and recreate it
            project.delete()
            dataset.add_project(Path(f'{download_dir}/{project.file.name}'))
