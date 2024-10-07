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

    _file_fields = {
        'mesh': 'core.DeepSSMTestingData.mesh',
        'particles': 'core.DeepSSMTestingData.particles',
    }

    project: Project
    image_type: str
    image_id: str
    mesh_source: Union[str, Path]
    particles_source: Union[str, Path]


class DeepSSMTrainingPair(ApiModel):
    _endpoint = 'deepssm-training-pair'

    _file_fields = {
        'particles': 'core.DeepSSMTrainingPair.particles',
        'scalar': 'core.DeepSSMTrainingPair.scalar',
        'mesh': 'core.DeepSSMTrainingPair.vtk',
    }

    project: Project
    particles_source: Union[str, Path]
    scalar_source: Union[str, Path]
    mesh_source: Union[str, Path]
    validation: bool
    example_type: str
    index: str


class DeepSSMTrainingImage(ApiModel):
    _endpoint = 'deepssm-training-image'

    _file_fields = {
        'image': 'core.DeepSSMTrainingImage.image',
    }

    project: Project
    image_source: Union[str, Path]
    index: str
    validation: bool


class DeepSSMAugPair(ApiModel):
    _endpoint = 'deepssm-aug-pair'

    _file_fields = {
        'mesh': 'core.DeepSSMAugPair.mesh',
        'image': 'core.DeepSSMAugPair.image',
        'particles': 'core.DeepSSMAugPair.particles',
    }

    project: Project
    sample_num: int
    mesh_source: Union[str, Path]
    image_source: Union[str, Path]
    particles_source: Union[str, Path]


class DeepSSMResult(ApiModel):
    _endpoint = 'deepssm-result'

    _file_fields = {
        'aug_visualization': 'core.DeepSSMResult.aug_visualization',
        'aug_total_data': 'core.DeepSSMResult.aug_total_data',
        'training_visualization': 'core.DeepSSMResult.training_visualization',
        'training_visualization_ft': 'core.DeepSSMResult.training_visualization_ft',
        'training_data_table': 'core.DeepSSMResult.training_data_table',
        'testing_distances': 'core.DeepSSMResult.testing_distances',
    }

    project: Project
    aug_visualization: Union[str, Path]
    aug_total_data: Union[str, Path]
    training_visualization: Union[str, Path]
    training_visualization_ft: Union[str, Path]
    training_data_table: Union[str, Path]
    testing_distances: Union[str, Path]


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
