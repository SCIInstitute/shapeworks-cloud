from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, Type, TypeVar

from pydantic import BaseModel

from .api import SwccSession
from .utils import download_file

ModelType = TypeVar('ModelType')


class ApiModelMixin:
    _endpoint: str

    @classmethod
    def from_id(cls: Type[ModelType], id: int) -> ModelType:
        pass


class BlobModel(BaseModel):
    id: int
    name: str
    blob: str
    subject: int
    particle_type: str
    chirality: str
    extension: str
    grooming_steps: str
    created: datetime
    modified: datetime

    def download(self, session: SwccSession, dest: Path):
        r = session.get(self.blob, stream=True)
        r.raise_for_status()
        download_file(r, dest, self.name, self.modified)


class ShapeModel(BaseModel):
    id: int
    name: str
    analyze: str
    correspondence: str
    transform: str
    created: datetime
    modified: datetime

    def download(self, session: SwccSession, dest: Path):
        dest.mkdir(exist_ok=True)
        for attr in ['analyze', 'correspondence', 'transform']:
            r = session.get(getattr(self, attr), stream=True)
            r.raise_for_status()
            Path(dest / self.name).mkdir(exist_ok=True)
            download_file(r, dest / self.name, attr, self.modified)


class Groomed(BlobModel):
    pass


class Segmentation(BlobModel):
    pass


class Particle(BlobModel):
    pass


class Dataset(BaseModel):
    id: int
    name: str
    groomed_pattern: str
    segmentation_pattern: str
    particles_pattern: str
    created: datetime
    num_segmentations: int
    num_groomed: int
    num_shape_models: int
    size: int

    @classmethod
    def from_id(cls, session: SwccSession, id_) -> Dataset:
        r = session.get(f'datasets/{id_}')
        r.raise_for_status()
        return cls(**r.json())

    @staticmethod
    def create(session: SwccSession, **kwargs) -> Dataset:
        r = session.post('datasets/', data=kwargs)
        r.raise_for_status()
        return Dataset(**r.json())

    @staticmethod
    def list(session: SwccSession) -> Iterable[Dataset]:
        r = session.get('datasets')
        r.raise_for_status()
        # TODO: pagination
        for dataset in r.json()['results']:
            yield Dataset(**dataset)

    @staticmethod
    def delete(session: SwccSession, id_):
        r = session.delete(f'datasets/{id_}/')
        r.raise_for_status()

    def segmentations(self, session: SwccSession) -> Iterable[Segmentation]:
        for result in session.all_paginated_results(f'datasets/{self.id}/segmentations'):
            yield Segmentation(**result)

    def groomed(self, session: SwccSession) -> Iterable[Groomed]:
        for result in session.all_paginated_results(f'datasets/{self.id}/groomed'):
            yield Groomed(**result)

    def shape_models(self, session: SwccSession) -> Iterable[ShapeModel]:
        for result in session.all_paginated_results(f'datasets/{self.id}/shape_models'):
            yield ShapeModel(**result)

    def particles(self, session: SwccSession, shape_model_id: int) -> Iterable[Particle]:
        for result in session.all_paginated_results(
            f'datasets/{self.id}/shape_models/{shape_model_id}/particles'
        ):
            yield Particle(**result)
