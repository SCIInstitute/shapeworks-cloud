# from io import BytesIO
# from pathlib import Path
# from tempfile import TemporaryDirectory
# from typing import List
from subprocess import Popen, PIPE

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from swcc.api import swcc_session
from swcc.models import Dataset


@shared_task
def groom(user_id, dataset_id):
    user = User.objects.get(id=user_id)
    token, _created = Token.objects.get_or_create(user=user)
    base_url = settings.API_URL
    with swcc_session(base_url=base_url) as session:
        session.set_token(token.key)
        d = Dataset.from_id(dataset_id)
        d.download('/tmp/ellipsoid_v0')
    process = Popen(
        ['/opt/shapeworks/bin/shapeworks', 'groom', '--name=/opt/django-project/'],
        stdout=PIPE,
        stderr=PIPE,
    )
    print(process.communicate())
    # TODO upload the groomed folder
