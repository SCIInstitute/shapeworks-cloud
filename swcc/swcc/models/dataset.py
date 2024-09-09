import re
from typing import Iterator, Union
from pathlib import Path

from pydantic.v1 import Field

from .api_model import ApiModel
from .utils import logger


class Dataset(ApiModel):
    _endpoint = 'datasets'
    _file_fields = {'file': 'core.Dataset.file'}

    file_source: Union[str, Path]
    name: str = Field(min_length=3, max_length=255)
    private: bool = False
    license: str = Field(min_length=3)
    description: str = Field(min_length=3)
    acknowledgement: str = Field(min_length=3)
    creator: str = ''
    keywords: str = ''
    contributors: str = ''
    publications: str = ''

    @property
    def subjects(self) -> Iterator:
        from .subject import Subject

        self.assert_remote()
        return Subject.list(dataset=self)

    @property
    def projects(self) -> Iterator:
        from .project import Project

        self.assert_remote()
        return Project.list(dataset=self)

    @property
    def segmentations(self) -> Iterator:
        for subject in self.subjects:
            for segmentation in subject.segmentations:
                yield segmentation

    @property
    def meshes(self) -> Iterator:
        for subject in self.subjects:
            for mesh in subject.meshes:
                yield mesh

    @property
    def contours(self) -> Iterator:
        for subject in self.subjects:
            for contour in subject.contours:
                yield contour

    @property
    def images(self) -> Iterator:
        for subject in self.subjects:
            for mesh in subject.images:
                yield mesh

    @property
    def landmarks(self) -> Iterator:
        for subject in self.subjects:
            for landmark in subject.landmarks:
                yield landmark

    @property
    def constraints(self) -> Iterator:
        for subject in self.subjects:
            for constraint in subject.constraints:
                yield constraint

    @classmethod
    def from_name(cls, name: str):
        results = cls.list(name=name)
        try:
            return next(results)
        except StopIteration:
            return None

    def has_data(self):
        for subject in self.subjects:
            if any(True for _ in subject.segmentations):
                return True
            if any(True for _ in subject.meshes):
                return True
            if any(True for _ in subject.contours):
                return True
            if any(True for _ in subject.images):
                return True
            if any(True for _ in subject.landmarks):
                return True
            if any(True for _ in subject.constraints):
                return True
        return False

    def force_create(self, backup=False):
        """
        Forcibly create the Dataset, even if it already exists.

        If backup=False (the default), then the existing Dataset is deleted.
        If backup=True, then the new Dataset will append an appropriate `-v*` version string to
        its name before creation.
        """
        from .project import Project

        old_dataset = Dataset.from_name(self.name)
        while old_dataset is not None:
            if not backup:
                # Delete the old dataset to resolve the collision
                old_dataset.delete()
            else:
                # Use a version suffix to resolve the collision
                version_regex = re.compile('(.*)-v([0-9]+)')
                match = version_regex.match(self.name)
                if match:
                    # The old name had a suffix, so increment it
                    name, old_version = match.groups()
                    logger.info('Trying a new name: %s, %s', name, old_version)
                    new_version = int(old_version) + 1
                    self.name = f'{name}-v{new_version}'
                else:
                    # The old name had no suffix, so append "-v1"
                    self.name = f'{self.name}-v1'
            # We have a new name now, but that new name might also conflict.
            # Keep looping until there is no conflict.
            old_dataset = Dataset.from_name(self.name)

        result = super().create()
        assert result

        new_dataset = Dataset.from_id(result.id)

        # for the new dataset, add one project file
        project = Project(
            name='First project',
            description='First project for this dataset',
            dataset=new_dataset,
            file_source=self.file_source,
        )
        project.create()

        # hacky solution for avoiding multiple implementations of IO
        project.delete()

        return new_dataset

    def download(self, path):
        for subject in self.subjects:
            subject.download(path)


Dataset.update_forward_refs()
