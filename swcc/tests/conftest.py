import os

import pytest

from swcc import models
from swcc.api import swcc_session

from .factories import file_context as _file_context


@pytest.fixture(autouse=True)
def file_context():
    with _file_context() as d:
        yield d


@pytest.fixture
def session():
    base_url = os.getenv('DJANGO_BASE_URL', 'http://localhost:8000/api/v1')
    username = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@noemail.com')
    password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'django-password')
    with swcc_session(base_url=base_url) as session:
        session.login(username, password)
        for dataset in models.Dataset.list():
            dataset.delete()

        for project in models.Project.list():
            project.delete()

        yield session
