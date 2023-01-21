import re
from typing import Iterator

from .api_model import ApiModel
from .utils import NonEmptyString, logger


class Dataset(ApiModel):
    _endpoint = 'datasets'

    name: NonEmptyString
    private: bool = False
    license: NonEmptyString
    description: NonEmptyString
    acknowledgement: NonEmptyString
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

    def force_create(self, backup=False):
        """
        Forcibly create the Dataset, even if it already exists.

        If backup=False (the default), then the existing Dataset is deleted.
        If backup=True, then the new Dataset will append an appropriate `-v*` version string to
        its name before creation.
        """
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
                    self.name = f'{name}-v{new_version}'  # type: ignore
                else:
                    # The old name had no suffix, so append "-v1"
                    self.name = f'{self.name}-v1'  # type: ignore
            # We have a new name now, but that new name might also conflict.
            # Keep looping until there is no conflict.
            old_dataset = Dataset.from_name(self.name)
        return self.create()

    def download(self, path):
        for subject in self.subjects:
            subject.download(path)
