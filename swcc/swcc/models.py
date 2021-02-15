from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

from pydantic import BaseModel
import requests

from .utils import download_file

if TYPE_CHECKING:
    from swcc.swcc import CliContext


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

    def download(self, ctx: CliContext, dest: Path):
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

    def download(self, ctx: CliContext, dest: Path):
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
    def from_id(cls, ctx: CliContext, id_) -> Dataset:
        r = ctx.session.get(f'datasets/{id_}')
        r.raise_for_status()
        return cls(**r.json())

    @staticmethod
    def create(ctx: CliContext, **kwargs) -> Dataset:
        r = ctx.session.post('datasets/', data=kwargs)
        r.raise_for_status()
        return Dataset(**r.json())

    @staticmethod
    def list(ctx: CliContext) -> Iterable[Dataset]:
        r = ctx.session.get('datasets')
        r.raise_for_status()
        # TODO: pagination
        for dataset in r.json()['results']:
            yield Dataset(**dataset)

    @staticmethod
    def delete(ctx: CliContext, id_):
        r = ctx.session.delete(f'datasets/{id_}/')
        r.raise_for_status()

    def segmentations(self, ctx: CliContext) -> Iterable[Segmentation]:
        for result in ctx.session.all_paginated_results(ctx, f'datasets/{self.id}/segmentations'):
            yield Segmentation(**result)

    def groomed(self, ctx: CliContext) -> Iterable[Groomed]:
        for result in ctx.session.all_paginated_results(ctx, f'datasets/{self.id}/groomed'):
            yield Groomed(**result)

    def shape_models(self, ctx: CliContext) -> Iterable[ShapeModel]:
        for result in ctx.session.all_paginated_results(ctx, f'datasets/{self.id}/shape_models'):
            yield ShapeModel(**result)

    def particles(self, ctx: CliContext, shape_model_id: int) -> Iterable[Particle]:
        for result in ctx.session.all_paginated_results(
            ctx, f'datasets/{self.id}/shape_models/{shape_model_id}/particles'
        ):
            yield Particle(**result)
