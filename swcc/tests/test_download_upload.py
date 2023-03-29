# This test requires that https://www.shapeworks-cloud.org/#/ is running
# This will fetch all datasets populated on the public server and attempt to
# upload them all to the local server
import random
import os
import filecmp
from tempfile import TemporaryDirectory

from swcc import models
from swcc.api import swcc_session

SAMPLE_SIZE = 3


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


class dircmp(filecmp.dircmp):
    def phase3(self):
        fcomp = filecmp.cmpfiles(self.left, self.right, self.common_files, shallow=False)
        self.same_files, self.diff_files, self.funny_files = fcomp


def is_same(dir1, dir2):
    compared = dircmp(dir1, dir2)
    different = (
        compared.left_only or compared.right_only or compared.diff_files or compared.funny_files
    )
    if different:
        return False
    for subdir in compared.common_dirs:
        if not is_same(os.path.join(dir1, subdir), os.path.join(dir2, subdir)):
            return False
    return True


def test_download_upload_cycle(session):
    with TemporaryDirectory() as temp_dir:
        all_projects = []

        # Download from public server
        download_dir = f'{temp_dir}/download'
        with swcc_session() as public_server_session:
            public_server_session.login('testuser@noemail.nil', 'cicdtest')
            all_projects = random.sample(list(models.Project.list()), SAMPLE_SIZE)
            for project in all_projects:
                project.download(download_dir)

        # Upload to local server
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

        # Redownload from local server
        redownload_dir = f'{temp_dir}/redownload'
        for project in all_projects:
            project.download(redownload_dir)

        # Test for file structure congruence
        assert is_same(download_dir, redownload_dir)

    for local_project, remote_project in zip(models.Project.list(), all_projects):
        local_repr = project_as_dict_repr(local_project)
        remote_repr = project_as_dict_repr(remote_project)
        assert local_repr == remote_repr
    assert len(list(models.Project.list())) == len(all_projects)
