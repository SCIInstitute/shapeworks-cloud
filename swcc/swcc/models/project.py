from __future__ import annotations

import json
from pathlib import Path
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

    def load_data(self, create=True):
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
            return self.load_data_from_json(file, create)
        else:
            raise Exception(f'Unknown format for {file} - expected .xlsx, .xls, .swproj, or .json')

    def load_data_from_json(self, file, create):
        contents = json.load(open(file))
        data = self.interpret_data(contents['data'])
        if create:
            for [subject, objects_by_domain] in data:
                self.create_objects_for_subject(subject, objects_by_domain)
        return data

    def interpret_data(self, input_data):
        output_data = []
        for entry in input_data:
            subjects = [s for s in self.project.dataset.subjects if s.name == entry.get('name')]
            if len(subjects) > 0:
                subject = subjects[0]
            else:
                subject = Subject(name=entry.get('name'), dataset=self.project.dataset).create()

            entry_values: Dict = {p: [] for p in expected_key_prefixes}
            entry_values['anatomy_types'] = []
            for key in entry.keys():
                prefixes = [p for p in expected_key_prefixes if key.startswith(p)]
                if len(prefixes) > 0:
                    entry_values[prefixes[0]].append(entry[key])
                    if prefixes[0] in ['shape', 'mesh', 'segmentation', 'contour', 'image']:
                        entry_values['anatomy_types'].append(key)
            objects_by_domain = {}
            for index, anatomy_type in enumerate(entry_values['anatomy_types']):
                objects_by_domain[anatomy_type] = {
                    k: v[index] if len(v) > index else v[0]
                    for k, v in entry_values.items()
                    if len(v) > 0
                }

            output_data.append(
                [
                    subject,
                    objects_by_domain,
                ]
            )
        return output_data

    def create_objects_for_subject(
        self,
        subject,
        objects_by_domain,
    ):
        def relative_path(filepath):
            if not self.project.file.path:
                return None
            return Path(
                self.project.file.path.parent, str(filepath).replace('../', '').replace('./', '')
            )

        with TemporaryDirectory() as temp_dir:
            for anatomy_type, objects in objects_by_domain.items():
                original_shape: Union[Mesh, Segmentation, Contour, None] = None
                groomed_shape: Union[GroomedMesh, GroomedSegmentation, None] = None
                world_particles_path = None
                local_particles_path = None
                constraints_path = None
                transform = None

                for key, value in objects.items():
                    if key == 'shape':
                        key = shape_file_type(Path(value)).__name__.lower()

                    if key == 'mesh':
                        original_shape = Mesh(
                            file=relative_path(value),
                            anatomy_type=anatomy_type,
                            subject=subject,
                        ).create()
                    elif key == 'segmentation':
                        original_shape = Segmentation(
                            file=relative_path(value),
                            anatomy_type=anatomy_type,
                            subject=subject,
                        ).create()
                        pass
                    elif key == 'contour':
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
                        if type(original_shape) == Mesh:
                            groomed_shape = self.project.add_groomed_mesh(
                                file=relative_path(value),
                                mesh=original_shape,
                            )
                        elif type(original_shape) == Segmentation:
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
                    if type(original_shape) == Mesh:
                        groomed_mesh = groomed_shape
                    elif type(original_shape) == Segmentation:
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
        data = self.load_data(create=False)

        download_mappings: Dict[str, List] = {
            'mesh': [{'set': list(self.project.dataset.meshes), 'attr': 'file'}],
            'segmentation': [{'set': list(self.project.dataset.segmentations), 'attr': 'file'}],
            'contour': [{'set': list(self.project.dataset.contours), 'attr': 'file'}],
            'image': [{'set': list(self.project.dataset.images), 'attr': 'file'}],
            'groomed': [
                {'set': list(self.project.groomed_meshes), 'attr': 'file'},
                {'set': list(self.project.groomed_segmentations), 'attr': 'file'},
            ],
            'local': [{'set': list(self.project.particles), 'attr': 'local'}],
            'world': [{'set': list(self.project.particles), 'attr': 'world'}],
            'landmarks': [{'set': list(self.project.dataset.landmarks), 'attr': 'file'}],
            'constraints': [{'set': list(self.project.dataset.constraints), 'attr': 'file'}],
        }

        for [_s, objects_by_domain] in data:
            for _a, objects in objects_by_domain.items():
                for key, value in objects.items():
                    if key == 'shape':
                        key = shape_file_type(Path(value)).__name__.lower()
                    match_name = Path(value).name
                    if key in download_mappings:
                        for mapping in download_mappings[key]:
                            for x in mapping['set']:
                                attr = getattr(x, mapping['attr'])
                                if str(attr) == match_name:
                                    relative_download(attr, value)

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
