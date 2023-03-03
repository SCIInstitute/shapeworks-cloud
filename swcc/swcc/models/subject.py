from pathlib import Path
from typing import Dict, Iterator, List, Optional

from .api_model import ApiModel
from .dataset import Dataset
from .other_models import Constraints, Contour, Image, Landmarks, Mesh, Segmentation
from .utils import NonEmptyString


class Subject(ApiModel):
    _endpoint = 'subjects'

    name: NonEmptyString
    dataset: Dataset
    groups: Optional[Dict[str, str]]

    @property
    def segmentations(self) -> Iterator[Segmentation]:
        return Segmentation.list(subject=self)

    @property
    def meshes(self) -> Iterator[Mesh]:
        return Mesh.list(subject=self)

    @property
    def contours(self) -> Iterator[Contour]:
        return Contour.list(subject=self)

    @property
    def images(self) -> Iterator[Image]:
        return Image.list(subject=self)

    @property
    def landmarks(self) -> Iterator[Landmarks]:
        return Landmarks.list(subject=self)

    @property
    def constraints(self) -> Iterator[Constraints]:
        return Constraints.list(subject=self)

    def add_segmentation(self, file: Path, anatomy_type: str) -> Segmentation:
        return Segmentation(file=file, anatomy_type=anatomy_type, subject=self).create()

    def add_mesh(self, file: Path, anatomy_type: str) -> Mesh:
        return Mesh(file=file, anatomy_type=anatomy_type, subject=self).create()

    def add_contour(self, file: Path, anatomy_type: str) -> Contour:
        return Contour(file=file, anatomy_type=anatomy_type, subject=self).create()

    def add_image(self, file: Path, modality: str) -> Image:
        return Image(file=file, modality=modality, subject=self).create()

    @classmethod
    def from_name_and_dataset(cls, name: str, dataset: Dataset):
        results = cls.list(name=name, dataset=dataset)
        try:
            return next(results)
        except StopIteration:
            return None

    def download(self, path):
        self.assert_remote()
        data_lists: List[Iterator] = [
            self.segmentations,
            self.meshes,
            self.contours,
            self.images,
            self.landmarks,
            self.constraints,
        ]
        for iterator in data_lists:
            for item in iterator:
                item.file.download(path)
