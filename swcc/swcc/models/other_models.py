from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

from pydantic.v1 import Field

from .api_model import ApiModel


class Segmentation(ApiModel):
    _endpoint = 'segmentations'

    file_source: Union[Path, str]
    anatomy_type: str = Field(min_length=1)
    subject: Subject

    @property
    def file(self):
        return File(self.file_source, field_id='core.Segmentation.file')


class Mesh(ApiModel):
    _endpoint = 'meshes'

    file_source: Union[Path, str]
    anatomy_type: str = Field(min_length=1)
    subject: Subject

    @property
    def file(self):
        return File(self.file_source, field_id='core.Mesh.file')


class Contour(ApiModel):
    _endpoint = 'contours'

    file_source: Union[Path, str]
    anatomy_type: str = Field(min_length=1)
    subject: Subject

    @property
    def file(self):
        return File(self.file_source, field_id='core.Contour.file')


class Image(ApiModel):
    _endpoint = 'images'

    file_source: Union[Path, str]
    modality: str
    subject: Subject


class GroomedSegmentation(ApiModel):
    _endpoint = 'groomed-segmentations'

    file_source: Union[Path, str]
    pre_cropping_source: Optional[Union[Path, str]] = None
    pre_alignment_source: Optional[Union[Path, str]] = None
    segmentation: Segmentation
    project: Project

    @property
    def file(self):
        return File(self.file_source, field_id='core.GroomedSegmentation.file')

    @property
    def pre_cropping(self):
        return File(self.pre_cropping_source, field_id='core.GroomedSegmentation.pre_cropping')

    @property
    def pre_alignment(self):
        return File(self.pre_alignment_source, field_id='core.GroomedSegmentation.pre_alignment')


class GroomedMesh(ApiModel):
    _endpoint = 'groomed-meshes'

    file_source: Union[Path, str]
    pre_cropping_source: Optional[Union[Path, str]] = None
    pre_alignment_source: Optional[Union[Path, str]] = None
    mesh: Mesh
    project: Project

    @property
    def file(self):
        return File(self.file_source, field_id='core.GroomedMesh.file')

    @property
    def pre_cropping(self):
        return File(self.pre_cropping_source, field_id='core.GroomedMesh.pre_cropping')

    @property
    def pre_alignment(self):
        return File(self.pre_alignment_source, field_id='core.GroomedMesh.pre_alignment')


class OptimizedParticles(ApiModel):
    _endpoint = 'optimized-particles'

    world_source: Optional[Union[Path, str]] = None
    local_source: Optional[Union[Path, str]] = None
    transform_source: Optional[Union[Path, str]] = None
    project: Project
    subject: Subject
    anatomy_type: str = Field(min_length=1)
    groomed_segmentation: Optional[GroomedSegmentation]
    groomed_mesh: Optional[GroomedMesh]

    @property
    def world(self):
        return File(self.world_source, field_id='core.OptimizedParticles.world')

    @property
    def local(self):
        return File(self.local_source, field_id='core.OptimizedParticles.local')

    @property
    def transform(self):
        return File(self.transform_source, field_id='core.OptimizedParticles.transform')


class Landmarks(ApiModel):
    _endpoint = 'landmarks'

    file_source: Union[Path, str]
    subject: Subject
    anatomy_type: str = Field(min_length=1)
    project: Project

    @property
    def file(self):
        return File(self.file_source, field_id='core.Landmarks.file')


class Constraints(ApiModel):
    _endpoint = 'constraints'

    file_source: Union[Path, str]
    subject: Subject
    anatomy_type: str = Field(min_length=1)
    optimized_particles: Optional[OptimizedParticles]

    @property
    def file(self):
        return File(self.file_source, field_id='core.Constraints.file')


class CachedAnalysisGroup(ApiModel):
    _endpoint = 'cached-analysis-group'

    file_source: Union[Path, str]
    particles_source: Optional[Union[Path, str]] = None
    name: str = Field(min_length=1)
    group1: str = Field(min_length=1)
    group2: str = Field(min_length=1)
    ratio: float

    @property
    def file(self):
        return File(self.file_source, field_id='core.CachedAnalysisGroup.file')

    @property
    def particles(self):
        return File(self.particles_source, field_id='core.CachedAnalysisGroup.particles')


class CachedAnalysisModePCA(ApiModel):
    _endpoint = 'cached-analysis-mode-pca'

    pca_value: float
    lambda_value: float
    file_source: Union[Path, str]
    particles_source: Optional[Union[Path, str]] = None

    @property
    def file(self):
        return File(self.file_source, field_id='core.CachedAnalysisModePCA.file')

    @property
    def particles(self):
        return File(self.particles_source, field_id='core.CachedAnalysisModePCA.particles')


class CachedAnalysisMode(ApiModel):
    _endpoint = 'cached-analysis-mode'

    mode: int
    eigen_value: float
    explained_variance: float
    cumulative_explained_variance: float
    pca_values: List[CachedAnalysisModePCA]


class CachedAnalysisMeanShape(ApiModel):
    _endpoint = 'cached-analysis-mean-shape'

    file_source: Union[Path, str]
    particles_source: Optional[Union[Path, str]] = None

    @property
    def file(self):
        return File(self.file_source, field_id='core.CachedAnalysisMeanShape.file')

    @property
    def particles(self):
        return File(self.particles_source, field_id='core.CachedAnalysisMeanShape.particles')


class CachedAnalysis(ApiModel):
    _endpoint = 'cached-analysis'

    mean_shapes: List[CachedAnalysisMeanShape]
    modes: List[CachedAnalysisMode]
    charts: List[dict]
    groups: Optional[List[CachedAnalysisGroup]]
    good_bad_angles: List[list]


from .project import Project  # noqa: E402
from .subject import Subject  # noqa: E402
from .file import File  # noqa: E402


Segmentation.update_forward_refs()
Mesh.update_forward_refs()
Contour.update_forward_refs()
Image.update_forward_refs()
GroomedSegmentation.update_forward_refs()
GroomedMesh.update_forward_refs()
OptimizedParticles.update_forward_refs()
Landmarks.update_forward_refs()
Constraints.update_forward_refs()
