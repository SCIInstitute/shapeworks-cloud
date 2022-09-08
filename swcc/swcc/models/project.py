from __future__ import annotations

import json
from pathlib import Path, PurePath
from tempfile import TemporaryDirectory

try:
    from typing import Any, Dict, Iterator, Literal, Optional, Union
except ImportError:
    from typing import (
        Any,
        Dict,
        Iterator,
        Optional,
        Union,
    )
    from typing_extensions import (  # type: ignore
        Literal,
    )

from pydantic import BaseModel

from .api_model import ApiModel
from .dataset import Dataset
from .file_type import FileType
from .other_models import GroomedMesh, GroomedSegmentation, Mesh, OptimizedShapeModel, Segmentation
from .subject import Subject
from .utils import FileIO, shape_file_type


class ProjectFileIO(BaseModel, FileIO):
    project: Project

    class Config:
        arbitrary_types_allowed = True

    def load_data(self):
        if (
            not self.project.file
            or not hasattr(self.project.file, 'path')
            or not self.project.file.path
        ):
            return
        file = self.project.file.path
        data = None
        if str(file).endswith('xlsx') or str(file).endswith('xlsx'):
            raise NotImplementedError('Convert spreadsheet file to excel before parsing')
        elif str(file).endswith('json') or str(file).endswith('swproj'):
            data, optimize = self.load_data_from_json(file)
        else:
            raise Exception(
                f'Unknown spreadsheet format in {file} - expected .xlsx, .xls, .swproj, or .json'
            )

    def load_data_from_json(self, file):
        contents = json.load(open(file))
        shape_model = self.project.add_shape_model(contents['optimize'])
        self.interpret_data(contents['data'], shape_model)
        return None, None

    def interpret_data(self, data, shape_model):
        segmentations = {
            PurePath(segmentation.file.name).stem: segmentation
            for segmentation in self.project.dataset.segmentations
        }
        meshes = {PurePath(mesh.file.name).stem: mesh for mesh in self.project.dataset.meshes}

        expected_key_prefixes = [
            'name',
            'shape',
            'groomed',
            'local_particles',
            'world_particles',
            'alignment',
            'procrustes',
        ]
        for entry in data:
            entry_values = {}
            for key in entry.keys():
                if not any(key.startswith(prefix) for prefix in expected_key_prefixes):
                    raise Exception(
                        f'Unexpected key "{key}" in data section, '
                        f'expected all keys to start with one of {expected_key_prefixes}'
                    )
                prefix = [p for p in expected_key_prefixes if key.startswith(p)][0]
                entry_values[prefix] = entry[key]
            self.interpret_data_row(
                segmentations,
                meshes,
                shape_model,
                Path(str(entry_values.get('shape'))),
                Path(str(entry_values.get('groomed'))),
                Path(str(entry_values.get('alignment'))),
                Path(str(entry_values.get('local_particles'))),
                Path(str(entry_values.get('world_particles'))),
            )

    def interpret_data_row(
        self,
        segmentations,
        meshes,
        shape_model,
        shape_file,
        groomed_file,
        alignment_file,
        local,
        world,
    ):
        groomed_segmentation = None
        groomed_mesh = None
        data_type = shape_file_type(shape_file)
        project_root = Path(str(self.project.file.path)).parent

        if groomed_file:
            if data_type == Segmentation:
                segmentation = segmentations.get(shape_file.stem)
                if not segmentation:
                    segmentation = Segmentation(
                        file=project_root / shape_file,
                        anatomy_type='shape',
                        subject=Subject(
                            name=shape_file.stem,
                            dataset=self.project.dataset
                        ).create()
                    ).create()
                groomed_segmentation = self.project.add_groomed_segmentation(
                    file=project_root / groomed_file,
                    segmentation=segmentation,
                )
            elif data_type == Mesh:
                mesh = meshes.get(shape_file.stem)
                if not mesh:
                    mesh = Mesh(
                        file=project_root / shape_file,
                        anatomy_type='shape',
                        subject=Subject(
                            name=shape_file.stem,
                            dataset=self.project.dataset
                        ).create()
                    ).create()
                groomed_mesh = self.project.add_groomed_mesh(
                    file=project_root / groomed_file,
                    mesh=mesh,
                )

        if alignment_file and local and world:
            with TemporaryDirectory() as dir:
                transform = Path(dir) / f'{shape_file.stem}.transform'
                with transform.open('w') as f:
                    f.write(str(project_root / alignment_file))

                shape_model.add_particles(
                    world=project_root / world,
                    local=project_root / local,
                    transform=transform,
                    groomed_segmentation=groomed_segmentation,
                    groomed_mesh=groomed_mesh,
                    constraints=None
                )


class Project(ApiModel):
    _endpoint = 'projects'

    file: FileType[Literal['core.Project.file']]
    keywords: str = ''
    description: str = ''
    dataset: Dataset

    def get_file_io(self):
        return ProjectFileIO(project=self)

    @property
    def groomed_segmentations(self) -> Iterator[GroomedSegmentation]:
        self.assert_remote()
        return GroomedSegmentation.list(project=self)

    @property
    def groomed_meshes(self) -> Iterator[GroomedMesh]:
        self.assert_remote()
        return GroomedMesh.list(project=self)

    def add_groomed_segmentation(
        self,
        file: Path,
        segmentation: Segmentation,
        pre_cropping: Optional[Path] = None,
        pre_alignment: Optional[Path] = None,
    ) -> GroomedSegmentation:
        return GroomedSegmentation(
            file=file,
            segmentation=segmentation,
            project=self,
            pre_cropping=pre_cropping,
            pre_alignment=pre_alignment,
        ).create()

    def add_groomed_mesh(
        self,
        file: Path,
        mesh: Mesh,
        pre_cropping: Optional[Path] = None,
        pre_alignment: Optional[Path] = None,
    ) -> GroomedMesh:
        return GroomedMesh(
            file=file,
            mesh=mesh,
            project=self,
            pre_cropping=pre_cropping,
            pre_alignment=pre_alignment,
        ).create()

    def create(self) -> Project:
        result = super().create()
        if self.file:
            self.get_file_io().load_data()
        # Load the new dataset so we get an appropriate file field
        assert result.id
        return Project.from_id(result.id)

    @property
    def shape_models(self) -> Iterator[OptimizedShapeModel]:
        self.assert_remote()
        return OptimizedShapeModel.list(project=self)

    def add_shape_model(self, parameters: Dict[str, Any]) -> OptimizedShapeModel:
        return OptimizedShapeModel(
            project=self,
            parameters=parameters,
        ).create()

    def download(self, path: Union[Path, str]):
        self.file.download(Path(path))
        data, optimize = self.get_file_io().load_data(interpret=False)

        shape_model = next(self.shape_models) if any(True for _ in self.shape_models) else None
        groomed_segmentations = {
            PurePath(gs.file.name).stem: gs for gs in self.groomed_segmentations
        }
        local_files = (
            {PurePath(p.local.name).stem: p for p in shape_model.particles} if shape_model else {}
        )

        for _, groomed_file, _, local, world, constraints in self.get_file_io()._iter_data_sheet(
            data, Path(path)
        ):
            if groomed_file and groomed_file.stem in groomed_segmentations:
                gs = groomed_segmentations[groomed_file.stem]
                gs.file.download(groomed_file.parent)
            if local and world and local.stem in local_files:
                particles = local_files[local.stem]
                particles.local.download(local.parent)
                particles.world.download(world.parent)
                if particles.constraints and constraints:
                    particles.constraints.download(constraints.parent)


ProjectFileIO.update_forward_refs()
