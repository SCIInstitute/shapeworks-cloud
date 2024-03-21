from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

from pydantic.v1 import Field

from .api_model import ApiModel


class Segmentation(ApiModel):
    _endpoint = 'segmentations'
    _file_fields = {'file': 'core.Segmentation.file'}

    file_source: Union[str, Path]
    anatomy_type: str = Field(min_length=1)
    subject: Subject


class Mesh(ApiModel):
    _endpoint = 'meshes'
    _file_fields = {'file': 'core.Mesh.file'}

    file_source: Union[str, Path]
    anatomy_type: str = Field(min_length=1)
    subject: Subject


class Contour(ApiModel):
    _endpoint = 'contours'
    _file_fields = {'file': 'core.Contour.file'}

    file_source: Union[str, Path]
    anatomy_type: str = Field(min_length=1)
    subject: Subject


class Image(ApiModel):
    _endpoint = 'images'
    _file_fields = {'file': 'core.Image.file'}

    file_source: Union[str, Path]
    modality: str
    subject: Subject


class GroomedSegmentation(ApiModel):
    _endpoint = 'groomed-segmentations'
    _file_fields = {
        'file': 'core.GroomedSegmentation.file',
        'pre_cropping': 'core.GroomedSegmentation.pre_cropping',
        'pre_alignment': 'core.GroomedSegmentation.pre_alignment',
    }

    file_source: Union[str, Path]
    pre_cropping_source: Optional[Union[str, Path]] = None
    pre_alignment_source: Optional[Union[str, Path]] = None
    segmentation: Segmentation
    project: Project


class GroomedMesh(ApiModel):
    _endpoint = 'groomed-meshes'
    _file_fields = {
        'file': 'core.GroomedMesh.file',
        'pre_cropping': 'core.GroomedMesh.pre_cropping',
        'pre_alignment': 'core.GroomedMesh.pre_alignment',
    }

    file_source: Union[str, Path]
    pre_cropping_source: Optional[Union[str, Path]] = None
    pre_alignment_source: Optional[Union[str, Path]] = None
    mesh: Mesh
    project: Project


class OptimizedParticles(ApiModel):
    _endpoint = 'optimized-particles'
    _file_fields = {
        'world': 'core.OptimizedParticles.world',
        'local': 'core.OptimizedParticles.local',
        'transform': 'core.OptimizedParticles.transform',
    }

    world_source: Optional[Union[str, Path]] = None
    local_source: Optional[Union[str, Path]] = None
    transform_source: Optional[Union[str, Path]] = None
    project: Project
    subject: Subject
    anatomy_type: str = Field(min_length=1)
    groomed_segmentation: Optional[GroomedSegmentation]
    groomed_mesh: Optional[GroomedMesh]


class Landmarks(ApiModel):
    _endpoint = 'landmarks'
    _file_fields = {'file': 'core.Landmarks.file'}

    file_source: Union[str, Path]
    subject: Subject
    anatomy_type: str = Field(min_length=1)
    project: Project


class Constraints(ApiModel):
    _endpoint = 'constraints'
    _file_fields = {'file': 'core.Constraints.file'}

    file_source: Union[str, Path]
    subject: Subject
    anatomy_type: str = Field(min_length=1)
    project: Project


class CachedAnalysisGroup(ApiModel):
    _endpoint = 'cached-analysis-group'
    _file_fields = {
        'file': 'core.CachedAnalysisGroup.file',
        'particles': 'core.CachedAnalysisGroup.particles',
    }

    file_source: Union[str, Path]
    particles_source: Optional[Union[str, Path]] = None
    name: str = Field(min_length=1)
    group1: str = Field(min_length=1)
    group2: str = Field(min_length=1)
    ratio: float


class CachedAnalysisModePCA(ApiModel):
    _endpoint = 'cached-analysis-mode-pca'
    _file_fields = {
        'file': 'core.CachedAnalysisModePCA.file',
        'particles': 'core.CachedAnalysisModePCA.particles',
    }

    pca_value: float
    lambda_value: float
    file_source: Union[str, Path]
    particles_source: Optional[Union[str, Path]] = None


class CachedAnalysisMode(ApiModel):
    _endpoint = 'cached-analysis-mode'

    mode: int
    eigen_value: float
    explained_variance: float
    cumulative_explained_variance: float
    pca_values: List[CachedAnalysisModePCA]


class CachedAnalysisMeanShape(ApiModel):
    _endpoint = 'cached-analysis-mean-shape'
    _file_fields = {
        'file': 'core.CachedAnalysisMeanShape.file',
        'particles': 'core.CachedAnalysisMeanShape.particles',
    }

    file_source: Union[str, Path]
    particles_source: Optional[Union[str, Path]] = None


class CachedAnalysis(ApiModel):
    _endpoint = 'cached-analysis'

    mean_shapes: List[CachedAnalysisMeanShape]
    modes: List[CachedAnalysisMode]
    charts: List[dict]
    groups: Optional[List[CachedAnalysisGroup]]
    good_bad_angles: List[list]


class DeepSSMTestingData(ApiModel):
    _endpoint = 'deepssm-testing-data'

    project: Project
    image_type: NonEmptyString
    image_id: int
    mesh: FileType[Literal['core.DeepSSMTestingData.mesh']]
    particles: FileType[Literal['core.DeepSSMTestingData.particles']]


class DeepSSMTrainingImage(ApiModel):
    _endpoint = 'deepssm-training-image'

    project: Project
    image: FileType[Literal['core.DeepSSMTrainingImage.image']]
    validation: bool


class DeepSSMAugPair(ApiModel):
    _endpoint = 'deepssm-aug-pair'

    project: Project
    sample_num: int
    mesh: Literal['core.DeepSSMAugPair.mesh']
    particles: Literal['core.DeepSSMAugPair.particles']


class DeepSSMResult(ApiModel):
    _endpoint = 'deepssm-result'

    project: Project
    aug_visualization: FileType[Literal['core.DeepSSMResult.aug_visualization']]
    training_visualization: FileType[Literal['core.DeepSSMResult.training_visualization']]
    training_visualization_ft: FileType[Literal['core.DeepSSMResult.training_visualization_ft']]
    training_data_table: FileType[Literal['core.DeepSSMResult.training_data_table']]
    testing_distances: FileType[Literal['core.DeepSSMResult.testing_distances']]


from .project import Project  # noqa: E402
from .subject import Subject  # noqa: E402

Segmentation.update_forward_refs()
Mesh.update_forward_refs()
Contour.update_forward_refs()
Image.update_forward_refs()
GroomedSegmentation.update_forward_refs()
GroomedMesh.update_forward_refs()
OptimizedParticles.update_forward_refs()
Landmarks.update_forward_refs()
Constraints.update_forward_refs()
