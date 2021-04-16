from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Type, TypeVar

from pydantic import BaseModel

from .api import SwccSession
from .utils import download_file, raise_for_status

ModelType = TypeVar('ModelType')


class ApiModelMixin:
    _endpoint: str

    @classmethod
    def from_id(cls: Type[ModelType], session: SwccSession, id: int) -> ModelType:
        pass

    @classmethod
    def list(cls: Type[ModelType], session: SwccSession) -> List[ModelType]:
        pass

    @classmethod
    def delete(cls, session: SwccSession, id_) -> None:
        r = session.delete(f'{cls._endpoint}/{id_}/')
        raise_for_status(r)


class TimeStampedModel(BaseModel, ApiModelMixin):
    id: int
    created: datetime
    modified: datetime

    _endpoint: str = ''


class GroomedSegmentationList(BaseModel):
    name: str
    blob: str
    mesh: Optional[str]


class GroomedSegmentation(TimeStampedModel):
    name: str
    blob: str
    mesh: Optional[str]

    def download(self, session: SwccSession, dest: Path):
        r = session.get(self.blob, stream=True)
        raise_for_status(r)
        download_file(r, dest, self.name, self.modified)


class GroomedDataset(TimeStampedModel):
    name: str
    num_segmentations: int

    _endpoint: str = 'groomed-datasets'

    # @staticmethod
    # def create(ctx: CliContext, name: str, segmentations: List[Path]) -> GroomedDataset:
    #     segmentation_blobs = [
    #         {
    #             'name': str(seg),
    #             'blob': upload_path(ctx, seg, 'core.GroomedSegmentation.blob'),
    #         }
    #         for seg in segmentations
    #     ]

    #     r = ctx.session.post(
    #         'groomed-datasets/',
    #         json={
    #             'name': name,
    #             'segmentations': segmentation_blobs,
    #         },
    #     )
    #     raise_for_status(r)
    #     return GroomedDataset(**r.json())


class Project(TimeStampedModel):
    name: str
    groomed_dataset: int

    @classmethod
    def create(cls, session: SwccSession, name: str, groomed_dataset: int):
        r = session.post('projects/', json={'name': name, 'groomed_dataset': groomed_dataset})
        raise_for_status(r)
        return Project(**r.json())


class Optimization(TimeStampedModel):
    project: int
    number_of_particles: int
    use_normals: bool
    normal_weight: float
    checkpointing_interval: int
    iterations_per_split: int
    optimization_iterations: int
    starting_regularization: float
    ending_regularization: float
    recompute_regularization_interval: int
    relative_weighting: float
    initial_relative_weighting: float
    procrustes_interval: int
    procrustes_scaling: bool

    @classmethod
    def create(cls, session: SwccSession, **kwargs):
        r = session.post('optimizations/', json=kwargs)
        raise_for_status(r)
        data = r.json()
        parameters = data.pop('parameters')
        return Optimization(**data, **parameters)
