from __future__ import annotations

from pathlib import Path

try:
    from typing import Any, Dict, Iterator, Literal, Optional
except ImportError:
    from typing import (
        Any,
        Dict,
        Iterator,
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


class OptimizedShapeModel(ApiModel):
    _endpoint = 'optimized-shape-models'

    project: Project
    parameters: Dict[str, Any]

    @property
    def particles(self) -> Iterator[OptimizedParticles]:
        return OptimizedParticles.list(shape_model=self)

    def add_particles(
        self,
        world: Path,
        local: Path,
        transform: Path,
        groomed_segmentation: Optional[GroomedSegmentation],
        groomed_mesh: Optional[GroomedMesh],
        constraints: Path,
    ) -> OptimizedParticles:
        return OptimizedParticles(
            world=world,
            local=local,
            transform=transform,
            shape_model=self,
            groomed_segmentation=groomed_segmentation,
            groomed_mesh=groomed_mesh,
            constraints=constraints,
        ).create()


class OptimizedParticles(ApiModel):
    _endpoint = 'optimized-particles'

    world: FileType[Literal['core.OptimizedParticles.world']]
    local: FileType[Literal['core.OptimizedParticles.local']]
    transform: FileType[Literal['core.OptimizedParticles.transform']]
    shape_model: OptimizedShapeModel
    groomed_segmentation: Optional[GroomedSegmentation]
    groomed_mesh: Optional[GroomedMesh]
    constraints: Optional[FileType[Literal['core.OptimizedParticles.constraints']]] = None


class OptimizedPCAModel(ApiModel):
    _endpoint = 'optimized-pca-model'

    mean_particles: FileType[Literal['core.OptimizedPCAModel.mean_particles']]
    pca_modes: FileType[Literal['core.OptimizedPCAModel.pca_modes']]
    eigen_spectrum: FileType[Literal['core.OptimizedPCAModel.eigen_spectrum']]
    shape_model: OptimizedShapeModel


from .project import Project  # noqa: E402
from .subject import Subject  # noqa: E402

Segmentation.update_forward_refs()
Mesh.update_forward_refs()
Image.update_forward_refs()
GroomedSegmentation.update_forward_refs()
GroomedMesh.update_forward_refs()
OptimizedShapeModel.update_forward_refs()
OptimizedParticles.update_forward_refs()
OptimizedPCAModel.update_forward_refs()
