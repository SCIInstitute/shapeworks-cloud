from __future__ import annotations

import json
from pathlib import Path, PurePath
from tempfile import TemporaryDirectory

try:
    from typing import Any, Dict, Iterator, List, Literal, Optional, Union
except ImportError:
    from typing import (
        Any,
        Dict,
        Iterator,
        List,
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
from .other_models import (
    CachedAnalysis,
    CachedAnalysisMode,
    CachedAnalysisModePCA,
    GroomedMesh,
    GroomedSegmentation,
    Mesh,
    OptimizedParticles,
    Segmentation,
)
from .subject import Subject
from .utils import FileIO, shape_file_type


class ProjectFileIO(BaseModel, FileIO):
    project: Project

    class Config:
        arbitrary_types_allowed = True

    def load_data(self, interpret=True):
        if (
            not self.project.file
            or not hasattr(self.project.file, 'path')
            or not self.project.file.path
        ):
            return
        file = self.project.file.path
        if str(file).endswith('xlsx') or str(file).endswith('xlsx'):
            raise NotImplementedError('Convert spreadsheet file to excel before parsing')
        elif str(file).endswith('json') or str(file).endswith('swproj'):
            return self.load_data_from_json(file, interpret)
        else:
            raise Exception(f'Unknown format for {file} - expected .xlsx, .xls, .swproj, or .json')

    def load_data_from_json(self, file, interpret):
        contents = json.load(open(file))
        if interpret:
            self.interpret_data(contents['data'])
        return contents['data'], contents['optimize']

    def interpret_data(self, data):
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
                            name=shape_file.stem, dataset=self.project.dataset
                        ).create(),
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
                            name=shape_file.stem, dataset=self.project.dataset
                        ).create(),
                    ).create()
                groomed_mesh = self.project.add_groomed_mesh(
                    file=project_root / groomed_file,
                    mesh=mesh,
                )

        with TemporaryDirectory() as dir:
            transform = Path(dir) / f'{shape_file.stem}.transform'
            with transform.open('w') as f:
                f.write(str(project_root / alignment_file))

            OptimizedParticles(
                world=project_root / world,
                local=project_root / local,
                transform=transform,
                groomed_segmentation=groomed_segmentation,
                groomed_mesh=groomed_mesh,
                constraints=None,
                project=self.project,
            ).create()

    def load_analysis_from_json(self, file_path):
        project_root = Path(str(self.project.file.path)).parent
        analysis_file_location = project_root / Path(file_path)
        contents = json.load(open(analysis_file_location))
        mean_shape_path = list(contents['mean'].values())[0][0]
        modes = [
            CachedAnalysisMode(
                mode=mode['mode'],
                eigen_value=mode['eigen_value'],
                explained_variance=mode['explained_variance'],
                cumulative_explained_variance=mode['cumulative_explained_variance'],
                pca_values=[
                    CachedAnalysisModePCA(
                        pca_value=pca['pca_value'],
                        lambda_value=pca['lambda'],
                        file=analysis_file_location.parent / Path(pca['meshes'][0]),
                    ).create()
                    for pca in mode['pca_values']
                ],
            ).create()
            for mode in contents['modes']
        ]
        return CachedAnalysis(
            mean_shape=analysis_file_location.parent / Path(mean_shape_path),
            modes=modes,
            charts=contents['charts'],
        ).create()


class Project(ApiModel):
    _endpoint = 'projects'

    file: FileType[Literal['core.Project.file']]
    keywords: str = ''
    description: str = ''
    dataset: Dataset
    # sent in as a filepath string, interpreted as CachedAnalysis object
    last_cached_analysis: Any

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
        file_io = self.get_file_io()
        if self.last_cached_analysis:
            self.last_cached_analysis = file_io.load_analysis_from_json(self.last_cached_analysis)

        result = super().create()
        if self.file:
            file_io.load_data()

        # Load the new dataset so we get an appropriate file field
        assert result.id
        return Project.from_id(result.id)

    @property
    def particles(self) -> Iterator[OptimizedParticles]:
        self.assert_remote()
        return OptimizedParticles.list(project=self)

    def add_particles(self, parameters: Dict[str, Any]) -> OptimizedParticles:
        return OptimizedParticles(project=self, **parameters).create()

    def download(self, path: Union[Path, str]):
        self.file.download(Path(path))
        data, optimize = self.get_file_io().load_data(interpret=False)
        groomed_shapes: List[Union[GroomedMesh, GroomedSegmentation]] = list(self.groomed_meshes)
        groomed_shapes += list(self.groomed_segmentations)
        for data_row in data:
            # TODO: Download related objects
            print(data_row, groomed_shapes)


ProjectFileIO.update_forward_refs()
