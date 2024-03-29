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


class CachedPrediction(ApiModel):
    _endpoint = 'cached-prediction'

    particles: Literal['core.CachedPrediction.particles']


class CachedExample(ApiModel):
    _endpoint = 'cached-example'

    train_particles: Literal['core.CachedExample.train_particles']
    train_scalars: Literal['core.CachedExample.train_scalars']
    validation_particles: Literal['core.CachedExample.validation_particles']
    validation_scalars: Literal['core.CachedExample.validation_scalars']


class CachedModelExamples(ApiModel):
    _endpoint = 'cached-model-examples'

    best: CachedExample
    median: CachedExample
    worst: CachedExample


class CachedModel(ApiModel):
    _endpoint = 'cached-model'

    configuration: Literal['core.CachedModel.configuration']
    best_model: Literal['core.CachedModel.best_model']
    final_model: Literal['core.CachedModel.final_model']
    examples: CachedModelExamples
    pca_predictions: Optional[List[CachedPrediction]]
    ft_predictions: Optional[List[CachedPrediction]]
    train_log_ft: Optional[Literal['core.CachedModel.train_log_ft']]
    best_model_ft: Optional[Literal['core.CachedModel.best_model_ft']]
    final_model_ft: Optional[Literal['core.CachedModel.final_model_ft']]


class CachedTensors(ApiModel):
    _endpoint = 'cached-tensors'

    train: Literal['core.CachedTensors.train']
    validation: Literal['core.CachedTensors.validation']
    test: Literal['core.CachedTensors.test']


class CachedDataLoaders(ApiModel):
    _endpoint = 'cached-data-loaders'

    mean_pca: Literal['core.CachedDataLoaders.mean_pca']
    std_pca: Literal['core.CachedDataLoaders.std_pca']
    test_names: Literal['core.CachedDataLoaders.test_names']
    tensors: CachedTensors


class CachedAugmentationPair(ApiModel):
    _endpoint = 'cached-augmentation-pair'

    file: Literal['core.CachedAugmentationPair.file']
    particles: Literal['core.CachedAugmentationPair.particles']


class CachedAugmentation(ApiModel):
    _endpoint = 'cached-augmentation'

    pairs: List[CachedAugmentationPair]
    total_data_csv: Literal['core.CachedAugmentation.total_data_csv']
    violin_plot: Literal['core.CachedAugmentation.violin_plot']


class CachedDeepSSM(ApiModel):
    _endpoint = 'cached-deep-ssm'

    augmentation: CachedAugmentation
    data_loaders: Optional[CachedDataLoaders]
    model: Optional[CachedModel]


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
