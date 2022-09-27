from __future__ import annotations

try:
    from typing import List, Literal, Optional
except ImportError:
    from typing import (
        List,
        Optional,
    )
    from typing_extensions import (  # type: ignore
        Literal,
    )

from .api_model import ApiModel
from .file_type import FileType
from .utils import NonEmptyString


class Segmentation(ApiModel):
    _endpoint = 'segmentations'

    file: FileType[Literal['core.Segmentation.file']]
    anatomy_type: NonEmptyString
    subject: Subject


class Mesh(ApiModel):
    _endpoint = 'meshes'

    file: FileType[Literal['core.Mesh.file']]
    anatomy_type: NonEmptyString
    subject: Subject


class Image(ApiModel):
    _endpoint = 'images'

    file: FileType[Literal['core.Image.file']]
    modality: str
    subject: Subject


class GroomedSegmentation(ApiModel):
    _endpoint = 'groomed-segmentations'

    file: FileType[Literal['core.GroomedSegmentation.file']]
    pre_cropping: Optional[FileType[Literal['core.GroomedSegmentation.pre_cropping']]] = None
    pre_alignment: Optional[FileType[Literal['core.GroomedSegmentation.pre_alignment']]] = None

    segmentation: Segmentation
    project: Project


class GroomedMesh(ApiModel):
    _endpoint = 'groomed-meshes'

    file: FileType[Literal['core.GroomedMesh.file']]
    pre_cropping: Optional[FileType[Literal['core.GroomedMesh.pre_cropping']]] = None
    pre_alignment: Optional[FileType[Literal['core.GroomedMesh.pre_alignment']]] = None

    mesh: Mesh
    project: Project


class OptimizedParticles(ApiModel):
    _endpoint = 'optimized-particles'

    world: FileType[Literal['core.OptimizedParticles.world']]
    local: FileType[Literal['core.OptimizedParticles.local']]
    transform: FileType[Literal['core.OptimizedParticles.transform']]
    project: Project
    groomed_segmentation: Optional[GroomedSegmentation]
    groomed_mesh: Optional[GroomedMesh]
    constraints: Optional[FileType[Literal['core.OptimizedParticles.constraints']]] = None


class CachedAnalysisModePCA(ApiModel):
    _endpoint = 'cached-analysis-mode-pca'

    pca_value: float
    lambda_value: float
    file: FileType[Literal['core.CachedAnalysisModePCA.file']]


class CachedAnalysisMode(ApiModel):
    _endpoint = 'cached-analysis-mode'

    mode: int
    eigen_value: float
    explained_variance: float
    cumulative_explained_variance: float
    pca_values: List[CachedAnalysisModePCA]


class CachedAnalysis(ApiModel):
    _endpoint = 'cached-analysis'

    mean_shape: FileType[Literal['core.CachedAnalysis.mean_shape']]
    modes: List[CachedAnalysisMode]
    charts: List[dict]


from .project import Project  # noqa: E402
from .subject import Subject  # noqa: E402

Segmentation.update_forward_refs()
Mesh.update_forward_refs()
Image.update_forward_refs()
GroomedSegmentation.update_forward_refs()
GroomedMesh.update_forward_refs()
OptimizedParticles.update_forward_refs()
