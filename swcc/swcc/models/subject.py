from pathlib import Path
from typing import Iterator

from .api_model import ApiModel
from .dataset import Dataset
from .other_models import Image, Mesh, Segmentation
from .utils import NonEmptyString


class Subject(ApiModel):
    _endpoint = 'subjects'

    name: NonEmptyString
    dataset: Dataset

    @property
    def segmentations(self) -> Iterator[Segmentation]:
        self.assert_remote()
        return Segmentation.list(subject=self)

    @property
    def meshes(self) -> Iterator[Mesh]:
        self.assert_remote()
        return Mesh.list(subject=self)

    @property
    def images(self) -> Iterator[Image]:
        self.assert_remote()
        return Image.list(subject=self)

    def add_segmentation(self, file: Path, anatomy_type: str) -> Segmentation:
        return Segmentation(file=file, anatomy_type=anatomy_type, subject=self).create()

    def add_mesh(self, file: Path, anatomy_type: str) -> Mesh:
        return Mesh(file=file, anatomy_type=anatomy_type, subject=self).create()

    def add_image(self, file: Path, modality: str) -> Image:
        return Image(file=file, modality=modality, subject=self).create()
