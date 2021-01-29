from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel
import requests

from .utils import download_file


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
    subject: int
    chirality: str
    grooming_steps: str
    extension: str

    def download(self, ctx, dest: Path):
        r = requests.get(self.blob, stream=True)
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

    def download(self, ctx, dest: Path):
        dest.mkdir(exist_ok=True)
        for attr in ['analyze', 'correspondence', 'transform']:
            r = requests.get(getattr(self, attr), stream=True)
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
    def from_id(cls, ctx, id_) -> Dataset:
        r = ctx.session.get(f'datasets/{id_}')
        r.raise_for_status()
        return cls(**r.json())

    @staticmethod
    def create(ctx, **kwargs) -> Dataset:
        r = ctx.session.post('datasets/', data=kwargs)
        r.raise_for_status()
        return Dataset(**r.json())

    @staticmethod
    def list(ctx) -> Iterable[Dataset]:
        r = ctx.session.get('datasets')
        r.raise_for_status()
        # TODO: pagination
        for dataset in r.json()['results']:
            yield Dataset(**dataset)

    @staticmethod
    def delete(ctx, id_):
        r = ctx.session.delete(f'datasets/{id_}/')
        r.raise_for_status()

    def segmentations(self, ctx) -> Iterable[Segmentation]:
        r = ctx.session.get(f'datasets/{self.id}/segmentations')
        r.raise_for_status()
        for segmentation in r.json()['results']:
            yield Segmentation(**segmentation)

    def groomed(self, ctx) -> Iterable[Groomed]:
        r = ctx.session.get(f'datasets/{self.id}/groomed')
        r.raise_for_status()
        for groomed in r.json()['results']:
            yield Groomed(**groomed)

    def shape_models(self, ctx) -> Iterable:
        r = ctx.session.get(f'datasets/{self.id}/shape_models')
        r.raise_for_status()
        for shape_model in r.json()['results']:
            yield ShapeModel(**shape_model)

    def particles(self, ctx, shape_model_id: int) -> Iterable[Particle]:
        r = ctx.session.get(f'datasets/{self.id}/shape_models/{shape_model_id}/particles')
        r.raise_for_status()
        for particle in r.json()['results']:
            yield Particle(**particle)
