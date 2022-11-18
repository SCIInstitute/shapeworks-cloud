from __future__ import annotations

from pathlib import Path
import re

try:
    from typing import Dict, Iterator, Literal, Optional, Union
except ImportError:
    from typing import (
        Dict,
        Iterator,
        Optional,
        Union,
    )
    from typing_extensions import (  # type: ignore
        Literal,
    )

from openpyxl import load_workbook
from pydantic import BaseModel

from .api_model import ApiModel
from .constants import expected_key_prefixes
from .file_type import FileType
from .utils import FileIO, NonEmptyString, logger, shape_file_type


class DataFileIO(BaseModel, FileIO):
    dataset: Dataset

    class Config:
        arbitrary_types_allowed = True

    def load_data(self, interpret=True):
        if (
            not self.dataset.file
            or not hasattr(self.dataset.file, 'path')
            or not self.dataset.file.path
        ):
            return
        file = self.dataset.file.path
        data = None
        if str(file).endswith('xlsx') or str(file).endswith('xls'):
            # openpyxl does not support CSV
            data = self.load_data_from_excel(file)
        else:
            raise Exception(f'Unknown format for {file} - expected .xlsx or .xls')
        if interpret and data is not None:
            self.interpret_data(data, file.parent)
        return data

    def load_data_from_excel(self, file):
        xls = load_workbook(str(file), read_only=True)
        if 'data' not in xls:
            raise Exception('`data` sheet not found')

        return xls['data'].values

    def interpret_data(self, data, root):
        from .other_models import Mesh, Segmentation
        from .subject import Subject

        headers = next(data)
        for header in headers:
            if not (header.startswith('shape_') or header.startswith('image_')):
                raise Exception(
                    f'Unknown datasheet format - expected "shape_" or "image_" prefix, found {header}'  # noqa: E501
                )
        # split each header into ('shape', anatomy_type) and ('image', modality) tuples
        column_info = [header.split('_', 1) for header in headers]
        subjects: Dict[str, Subject] = {}
        found = False
        for row in data:
            subject = None
            for i, cell in enumerate(row):
                if not cell:
                    continue
                file_type, domain = column_info[i]
                file_path: Path = root / cell

                # Use the file name in the first cell as the subject name
                if subject is None:
                    subject_name = file_path.stem
                    if subject_name not in subjects:
                        subjects[subject_name] = self.dataset.add_subject(subject_name)
                    subject = subjects[subject_name]

                if file_type in expected_key_prefixes:
                    shape_file = file_path
                    if not shape_file.exists():
                        raise Exception(f'Could not find shape file at "{shape_file}"')
                    data_type = shape_file_type(shape_file)
                    if data_type == Segmentation:
                        subject.add_segmentation(file=shape_file, anatomy_type=domain)
                    elif data_type == Mesh:
                        subject.add_mesh(file=shape_file, anatomy_type=domain)
                    found = True
                elif file_type == 'image':
                    image_file = file_path
                    if not image_file.exists():
                        raise Exception(f'Could not find image file at "{image_file}"')
                    subject.add_image(file=image_file, modality=domain)
                    found = True
        if not found:
            raise Exception('Did not find any shape or image files in data sheet')


class Dataset(ApiModel):
    _endpoint = 'datasets'

    name: NonEmptyString
    file: Optional[FileType[Literal['core.Dataset.file']]] = None
    license: NonEmptyString
    description: NonEmptyString
    acknowledgement: NonEmptyString
    keywords: str = ''
    contributors: str = ''
    publications: str = ''

    def __repr_args__(self: BaseModel):
        return [
            (key, value)
            for key, value in self.__dict__.items()
            if key
            not in {
                'license',
                'description',
                'acknowledgement',
                'keywords',
                'contributors',
                'publications',
            }
        ]

    def get_file_io(self):
        return DataFileIO(dataset=self)

    @property
    def subjects(self) -> Iterator:
        from .subject import Subject

        self.assert_remote()
        return Subject.list(dataset=self)

    def add_subject(self, name: str):
        from .subject import Subject

        return Subject(name=name, dataset=self).create()

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

    def add_project(self, file: Path, keywords: str = '', description: str = ''):
        from .project import Project

        return Project(
            file=file,
            keywords=keywords,
            description=description,
            dataset=self,
            last_cached_analysis=None,
        ).create()

    @classmethod
    def from_name(cls, name: str) -> Optional[Dataset]:
        results = cls.list(name=name)
        try:
            return next(results)
        except StopIteration:
            return None

    def create(self) -> Dataset:
        result = super().create()
        if self.file:
            self.get_file_io().load_data()
        # Load the new dataset so we get an appropriate file field
        assert result.id
        return Dataset.from_id(result.id)

    def download(self, path: Union[Path, str]):
        self.assert_remote()
        path = Path(path)
        dataset_file = None
        if self.file:
            dataset_file = self.file.download(path)
        for project in self.projects:
            project.download(path)
        if not dataset_file:
            return
        data = self.get_file_io().load_data(interpret=False)
        for subject in self.subjects:
            row = next(entry for entry in data if subject.name == Path(entry[0]).stem)
            for segmentation in subject.segmentations:
                segmentation.file.download(path / Path(row[0]).parent)
            for mesh in subject.meshes:
                mesh.file.download(path / Path(row[0]).parent)
            for image in subject.images:
                image.file.download(path / Path(row[1]).parent)


DataFileIO.update_forward_refs()
