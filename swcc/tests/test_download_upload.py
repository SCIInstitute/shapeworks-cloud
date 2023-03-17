# This test requires that https://www.shapeworks-cloud.org/#/ is running
# This will fetch all datasets populated on the public server and attempt to
# upload them all to the local server
import random
from tempfile import TemporaryDirectory

from swcc import models
from swcc.api import swcc_session


def project_as_dict_repr(project):
    project_repr = dict(project)
    project_repr['dataset'] = dict(project_repr['dataset'])

    # remove keys that are expected to differ between servers
    del project_repr['id']
    del project_repr['file']
    del project_repr['dataset']['id']
    del project_repr['dataset']['creator']
    del project_repr['last_cached_analysis']
    return project_repr


def test_download_upload_cycle(session):
    with TemporaryDirectory() as download_dir:
        all_projects = []

        with swcc_session() as public_server_session:
            public_server_session.login('testuser@noemail.nil', 'cicdtest')
            all_projects = random.sample(list(models.Project.list()), 1)
            for project in all_projects:
                project.download(download_dir)

        for project in all_projects:
            d = models.Dataset(
                name=project.dataset.name,
                description=project.dataset.description,
                license=project.dataset.license,
                acknowledgement=project.dataset.acknowledgement,
                keywords=project.dataset.keywords,
                contributors=project.dataset.contributors,
                publications=project.dataset.publications,
            ).force_create()
            models.Project(
                dataset=d,
                file=project.file.path,
                description=project.description,
            ).create()

    for local_project, remote_project in zip(models.Project.list(), all_projects):
        local_repr = project_as_dict_repr(local_project)
        remote_repr = project_as_dict_repr(remote_project)
        assert local_repr == remote_repr
    assert len(list(models.Project.list())) == len(all_projects)
