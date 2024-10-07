from __future__ import annotations
import re
from pydantic.v1 import BaseModel, Field

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, Iterator, Union
import warnings

from .api_model import ApiModel
from .constants import expected_key_prefixes, required_key_prefixes
from .utils import FileIO, print_progress_bar, shape_file_type, logger


class DatasetFileIO(BaseModel, FileIO):
    dataset: Dataset

    class Config:
        arbitrary_types_allowed = True

    def load_data(self, create=True):
        if (
            not hasattr(self.dataset.file, 'path')
            or not self.dataset.file.path
        ):
            file = Path(str(self.dataset.file))
        else:
            file = self.dataset.file.path
        if str(file).endswith('xlsx') or str(file).endswith('xlsx'):
            raise NotImplementedError('Convert spreadsheet file to json/swproj before parsing')
        elif str(file).endswith('json') or str(file).endswith('swproj'):
            return self.load_data_from_json(file, create)
        else:
            raise Exception(f'Unknown format for {file} - expected .swproj, or .json')

    def load_data_from_json(self, file, create):
        contents = json.load(open(file))
        data = self.interpret_data(contents['data'])

        if self.dataset.has_data():
            if len(data) != len(list(self.dataset.subjects)):
                raise Exception(
                    f'''Number of subjects in uploaded project ({len(list(self.dataset.subjects))})
                    does not match number of subjects in the dataset ({len(data)}).'''
                )
        if create:
            print(f'Uploading files for {len(data)} subjects...')
            i = 0
            total_progress_steps = len(data)
            print_progress_bar(i, total_progress_steps)
            for [subject, objects_by_domain] in data:
                i += 1
                self.create_objects_for_subject(subject, objects_by_domain)
                print_progress_bar(i, total_progress_steps)
            print()
        return data

    def create_objects_for_subject(
        self,
        subject,
        objects_by_domain,
    ):
        from .other_models import (
            Contour,
            Image,
            Mesh,
            Segmentation,
        )

        def relative_path(filepath):
            if not self.dataset.file.path:
                return None
            return Path(
                self.dataset.file.path.parent, str(filepath).replace('../', '').replace('./', '')
            )

        with TemporaryDirectory() as temp_dir:
            for anatomy_id, objects in objects_by_domain.items():
                transform = None

                for key, value in objects.items():
                    if key == 'shape':
                        key = shape_file_type(Path(value)).__name__.lower()

                    if key == 'mesh':
                        Mesh(
                            file_source=relative_path(value),
                            anatomy_type=anatomy_id,
                            subject=subject,
                        ).create()
                    elif key == 'segmentation':
                        Segmentation(
                            file_source=relative_path(value),
                            anatomy_type=anatomy_id,
                            subject=subject,
                        ).create()
                        pass
                    elif key == 'contour':
                        Contour(
                            file_source=relative_path(value),
                            anatomy_type=anatomy_id,
                            subject=subject,
                        ).create()
                    elif key == 'image':
                        Image(
                            file_source=relative_path(value),
                            modality=anatomy_id,
                            subject=subject,
                        ).create()
                    elif key == 'alignment':
                        transform = Path(temp_dir) / 'transform'
                        with transform.open('w') as f:
                            f.write(value)

    def interpret_data(self, input_data):
        from .subject import Subject
        output_data = []
        for entry in input_data:
            subjects = [s for s in self.dataset.subjects if s.name == entry.get('name')]
            if len(subjects) > 0:
                subject = subjects[0]
            else:
                groups_dict = {
                    k.replace('group_', ''): v for k, v in entry.items() if k.startswith('group_')
                }
                subject = Subject(
                    name=entry.get('name'), groups=groups_dict, dataset=self.dataset
                ).create()

            objects_by_domain: Dict[str, Dict] = {}
            for key in entry.keys():
                prefixes = [p for p in expected_key_prefixes if key.startswith(p)]
                if len(prefixes) > 0:
                    prefix = prefixes[0]
                    anatomy_id = 'anatomy' + key
                    anatomy_id = anatomy_id.replace(prefix, '').replace('_particles', '')
                    # Only create a new domain object if a shape exists for that suffix
                    if anatomy_id not in objects_by_domain:
                        if prefix in required_key_prefixes:
                            objects_by_domain[anatomy_id] = {}
                        else:
                            warnings.warn(
                                f'No shape exists for {anatomy_id}. Cannot create {key}.',
                                stacklevel=2,
                            )
                            continue
                    objects_by_domain[anatomy_id][prefix] = (
                        entry[key].replace('../', '').replace('./', '')
                    )
            output_data.append(
                [
                    subject,
                    objects_by_domain,
                ]
            )
        return output_data


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

    def get_file_io(self):
        return DatasetFileIO(dataset=self)

    @property
    def subjects(self) -> Iterator:
        from .subject import Subject  # noqa: E402

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

        # HACKY SOLUTION FOR PROJECT FILEIO
        # for the new dataset, add one project file
        # project = Project(
        #     name='First project',
        #     description='First project for this dataset',
        #     dataset=new_dataset,
        #     file_source=self.file_source,
        # )
        # project.create()

        # project.delete()

        # dataset fileio
        dataset_io = self.get_file_io()
        dataset_io.load_data(create=True)

        return new_dataset

    def download(self, path):
        for subject in self.subjects:
            subject.download(path)


DatasetFileIO.update_forward_refs()
Dataset.update_forward_refs()
