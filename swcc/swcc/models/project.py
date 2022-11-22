from __future__ import annotations

import json
from pathlib import Path
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
from .constants import expected_key_prefixes
from .dataset import Dataset
from .file_type import FileType
from .other_models import (
    CachedAnalysis,
    CachedAnalysisMode,
    CachedAnalysisModePCA,
    Constraints,
    Contour,
    GroomedMesh,
    GroomedSegmentation,
    Image,
    Landmarks,
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
            file = Path(str(self.project.file))
        else:
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
        for entry in data:
            entry_values = {}
            anatomy_type = 'shape'
            for key in entry.keys():
                prefixes = [p for p in expected_key_prefixes if key.startswith(p)]
                if len(prefixes) > 0:
                    entry_values[prefixes[0]] = entry[key]
                    if prefixes[0] == 'shape':
                        anatomy_type = key
            self.create_objects_from_row(
                anatomy_type,
                entry_values,
            )

    def create_objects_from_row(
        self,
        anatomy_type,
        row,
    ):
        def relative_path(filepath):
            return Path(
                self.project.file.path.parent, str(filepath).replace('../', '').replace('./', '')
            )

        with TemporaryDirectory() as temp_dir:

            original_shape = None
            original_shape_type = None
            groomed_shape = None
            world_particles_path = None
            local_particles_path = None
            constraints_path = None
            transform = None

            subject = Subject(name=row.get('name'), dataset=self.project.dataset).create()

            for key, value in row.items():
                if key == 'shape':
                    key = shape_file_type(Path(value)).__name__.lower()

                if key == 'mesh':
                    original_shape_type = 'mesh'
                    original_shape = Mesh(
                        file=relative_path(value),
                        anatomy_type=anatomy_type,
                        subject=subject,
                    ).create()
                elif key == 'segmentation':
                    original_shape_type = 'segmentation'
                    original_shape = Segmentation(
                        file=relative_path(value),
                        anatomy_type=anatomy_type,
                        subject=subject,
                    ).create()
                    pass
                elif key == 'contour':
                    original_shape_type = 'contour'
                    original_shape = Contour(
                        file=relative_path(value),
                        anatomy_type=anatomy_type,
                        subject=subject,
                    ).create()
                elif key == 'image':
                    Image(
                        file=relative_path(value),
                        modality=anatomy_type,
                        subject=subject,
                    ).create()
                elif key == 'groomed':
                    if original_shape_type == 'mesh':
                        groomed_shape = self.project.add_groomed_mesh(
                            file=relative_path(value),
                            mesh=original_shape,
                        )
                    elif original_shape_type == 'segmentation':
                        groomed_shape = self.project.add_groomed_segmentation(
                            file=relative_path(value),
                            segmentation=original_shape,
                        )
                elif key == 'local':
                    local_particles_path = relative_path(value)
                elif key == 'world':
                    world_particles_path = relative_path(value)
                elif key == 'alignment':
                    transform = Path(temp_dir) / 'transform'
                    with transform.open('w') as f:
                        f.write(value)
                elif key == 'landmarks':
                    Landmarks(
                        file=relative_path(value),
                        subject=subject,
                    ).create()
                elif key == 'constraints':
                    constraints_path = relative_path(value)
                # elif key == 'procrustes':
                #     pass

            if world_particles_path or local_particles_path:
                groomed_mesh = None
                groomed_segmentation = None
                if original_shape_type == 'mesh':
                    groomed_mesh = groomed_shape
                elif original_shape_type == 'segmentation':
                    groomed_segmentation = groomed_shape
                particles = OptimizedParticles(
                    world=world_particles_path,
                    local=local_particles_path,
                    transform=transform,
                    groomed_segmentation=groomed_segmentation,
                    groomed_mesh=groomed_mesh,
                    project=self.project,
                ).create()
                if constraints_path:
                    Constraints(
                        file=constraints_path, subject=subject, optimized_particles=particles
                    ).create()

    def download_all(self, location):
        def relative_path(filepath):
            return Path(
                location,
                str('/'.join(filepath.split('/')[:-1])).replace('../', '').replace('./', ''),
            )

        def relative_download(file, resolve):
            if not file:
                return
            file.download(relative_path(resolve))

        relative_download(self.project.file, '')
        data, optimize = self.load_data(interpret=False)

        for entry in data:
            row = {}
            for key in entry.keys():
                prefixes = [p for p in expected_key_prefixes if key.startswith(p)]
                if len(prefixes) > 0:
                    row[prefixes[0]] = entry[key]

            for key, value in row.items():
                match_name = Path(value).name
                if key == 'shape':
                    key = shape_file_type(Path(value)).__name__.lower()

                if key == 'mesh':
                    for m in self.project.dataset.meshes:
                        if str(m.file) == match_name:
                            relative_download(m.file, value)
                elif key == 'segmentation':
                    for s in self.project.dataset.segmentations:
                        if str(s.file) == match_name:
                            relative_download(s.file, value)
                elif key == 'contour':
                    for c in self.project.dataset.contours:
                        if str(c.file) == match_name:
                            relative_download(c.file, value)
                elif key == 'image':
                    for i in self.project.dataset.images:
                        if str(i.file) == match_name:
                            relative_download(i.file, value)
                elif key == 'groomed':
                    for g in self.project.groomed_meshes:
                        if str(g.file) == match_name:
                            relative_download(g.file, value)
                    for g in self.project.groomed_segmentations:
                        if str(g.file) == match_name:
                            relative_download(g.file, value)
                elif key == 'local':
                    for p in self.project.particles:
                        if str(p.local) == match_name:
                            relative_download(p.local, value)
                elif key == 'world':
                    for p in self.project.particles:
                        if str(p.world) == match_name:
                            relative_download(p.world, value)
                elif key == 'landmarks':
                    for lm in self.project.dataset.landmarks:
                        if str(lm.file) == match_name:
                            relative_download(lm.file, value)
                elif key == 'constraints':
                    for c in self.project.dataset.constraints:
                        if str(c.file) == match_name:
                            relative_download(c.file, value)

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
    last_cached_analysis: Optional[Any]

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

    @property
    def particles(self) -> Iterator[OptimizedParticles]:
        self.assert_remote()
        return OptimizedParticles.list(project=self)

    def add_particles(self, parameters: Dict[str, Any]) -> OptimizedParticles:
        return OptimizedParticles(project=self, **parameters).create()

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

    def download(self, path: Union[Path, str]):
        self.get_file_io().download_all(path)


ProjectFileIO.update_forward_refs()
