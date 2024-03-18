from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, Iterator, Optional, Union
import warnings

from pydantic.v1 import BaseModel
import requests

from ..api import current_session
from .api_model import ApiModel
from .constants import expected_key_prefixes, required_key_prefixes
from .dataset import Dataset
from .file import File
from .other_models import (
    CachedAnalysis,
    CachedAnalysisGroup,
    CachedAnalysisMeanShape,
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
from .utils import FileIO, print_progress_bar, raise_for_status, shape_file_type


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
            print(f'Uploading files for {len(data)} subjects...')
            i = 0
            total_progress_steps = len(data)
            print_progress_bar(i, total_progress_steps)
            for [subject, objects_by_domain] in data:
                i += 1
                self.create_objects_for_subject(subject, objects_by_domain)
                print_progress_bar(i, total_progress_steps)
            print()
        return data

    def interpret_data(self, input_data):
        output_data = []
        for entry in input_data:
            subjects = [s for s in self.project.dataset.subjects if s.name == entry.get('name')]
            if len(subjects) > 0:
                subject = subjects[0]
            else:
                groups_dict = {
                    k.replace('group_', ''): v for k, v in entry.items() if k.startswith('group_')
                }
                subject = Subject(
                    name=entry.get('name'), groups=groups_dict, dataset=self.project.dataset
                ).create()

            objects_by_domain: Dict[str, Dict] = {}
            for key in entry.keys():
                prefixes = [p for p in expected_key_prefixes if key.startswith(p)]
                if len(prefixes) > 0:
                    prefix = prefixes[0]
                    anatomy_id = 'anatomy' + key
                    anatomy_id = anatomy_id.replace(prefix, '').replace('_particles', '')
                    # Only create a new domain object if a shape exists for that suffix
                    if anatomy_id not in objects_by_domain:
                        if prefix in required_key_prefixes:
                            objects_by_domain[anatomy_id] = {}
                        else:
                            warnings.warn(
                                f'No shape exists for {anatomy_id}. Cannot create {key}.',
                                stacklevel=2,
                            )
                            continue
                    objects_by_domain[anatomy_id][prefix] = (
                        entry[key].replace('../', '').replace('./', '')
                    )
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
            for anatomy_id, objects in objects_by_domain.items():
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
                            file_source=relative_path(value),
                            anatomy_type=anatomy_id,
                            subject=subject,
                        ).create()
                    elif key == 'segmentation':
                        original_shape = Segmentation(
                            file_source=relative_path(value),
                            anatomy_type=anatomy_id,
                            subject=subject,
                        ).create()
                        pass
                    elif key == 'contour':
                        original_shape = Contour(
                            file_source=relative_path(value),
                            anatomy_type=anatomy_id,
                            subject=subject,
                        ).create()
                    elif key == 'image':
                        Image(
                            file_source=relative_path(value),
                            modality=anatomy_id,
                            subject=subject,
                        ).create()
                    elif key == 'groomed':
                        if type(original_shape) == Mesh:
                            groomed_shape = self.project.add_groomed_mesh(
                                file_source=relative_path(value),
                                mesh=original_shape,
                            )
                        elif type(original_shape) == Segmentation:
                            groomed_shape = self.project.add_groomed_segmentation(
                                file_source=relative_path(value),
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
                    elif key == 'landmarks_file':
                        Landmarks(
                            file_source=relative_path(value),
                            subject=subject,
                            project=self.project,
                            anatomy_type=anatomy_id,
                        ).create()
                    elif key == 'constraints':
                        constraints_path = relative_path(value)
                    # elif key == 'procrustes':
                    #     pass
                if world_particles_path or local_particles_path:
                    groomed_mesh = None
                    groomed_segmentation = None
                    if type(groomed_shape) == GroomedMesh:
                        groomed_mesh = groomed_shape
                    elif type(groomed_shape) == GroomedSegmentation:
                        groomed_segmentation = groomed_shape
                    OptimizedParticles(
                        world_source=world_particles_path,
                        local_source=local_particles_path,
                        transform_source=transform,
                        groomed_segmentation=groomed_segmentation,
                        groomed_mesh=groomed_mesh,
                        project=self.project,
                        subject=subject,
                        anatomy_type=anatomy_id,
                    ).create()
                if constraints_path:
                    with open(constraints_path) as f:
                        constraints_contents = json.load(f)
                    if constraints_contents:
                        Constraints(
                            file_source=constraints_path,
                            subject=subject,
                            project=self.project,
                            anatomy_type=anatomy_id,
                        ).create()

    def load_analysis_from_json(self, file_path):
        project_root = Path(str(self.project.file.path)).parent
        analysis_file_location = project_root / Path(file_path)
        contents = json.load(open(analysis_file_location))
        if contents['mean'] and contents['mean']['meshes']:
            mean_shapes_cache = []
            mean_shapes = []
            for mean_shape in contents['mean']['meshes']:
                mean_shapes.append(analysis_file_location.parent / Path(mean_shape))

            if 'particle_files' in contents['mean']:
                mean_particles = []
                for mean_particle_path in contents['mean']['particle_files']:
                    mean_particles.append(analysis_file_location.parent / Path(mean_particle_path))

                for i in range(len(mean_shapes)):
                    cams = CachedAnalysisMeanShape(
                        file_source=mean_shapes[i],
                        particles_source=mean_particles[i] if mean_particles else None,
                    ).create()
                    mean_shapes_cache.append(cams)

            modes = []
            for mode in contents['modes']:
                pca_values = []
                for pca in mode['pca_values']:
                    i = 0
                    while (
                        'meshes' in pca
                        and len(pca['meshes']) > i
                        and 'particles' in pca
                        and len(pca['particles']) > i
                    ):
                        cam_pca = CachedAnalysisModePCA(
                            pca_value=pca['pca_value'],
                            lambda_value=pca['lambda'],
                            file_source=analysis_file_location.parent / Path(pca['meshes'][i]),
                            particles_source=analysis_file_location.parent
                            / Path(pca['particles'][i]),
                        ).create()
                        pca_values.append(cam_pca)
                        i += 1
                if len(pca_values) > 0:
                    cam = CachedAnalysisMode(
                        mode=mode['mode'],
                        eigen_value=mode['eigen_value'],
                        explained_variance=mode['explained_variance'],
                        cumulative_explained_variance=mode['cumulative_explained_variance'],
                        pca_values=pca_values,
                    ).create()
                    modes.append(cam)

            if len(modes) > 0:
                groups_cache = []
                if contents['groups']:
                    for group in contents['groups']:
                        for values in group['values']:
                            for i in range(0, len(values['meshes'])):
                                cag = CachedAnalysisGroup(
                                    name=group['name'],
                                    group1=group['group1'],
                                    group2=group['group2'],
                                    ratio=values['ratio'],
                                    file_source=(
                                        analysis_file_location.parent / Path(values['meshes'][i])
                                    ),
                                    particles_source=(
                                        analysis_file_location.parent / Path(values['particles'][i])
                                    ),
                                ).create()

                                groups_cache.append(cag)
                return CachedAnalysis(
                    mean_shapes=mean_shapes_cache,
                    modes=modes,
                    charts=contents['charts'],
                    groups=groups_cache,
                    good_bad_angles=contents['good_bad_angles'],
                ).create()


class Project(ApiModel):
    _endpoint = 'projects'
    _file_fields = {'file': 'core.Project.file'}

    private: bool = False
    readonly: bool = False
    name: str = 'My Project'
    file_source: Union[str, Path]
    keywords: str = ''
    description: str = ''
    creator: Optional[str] = ''
    dataset: Dataset
    # sent in as a filepath string, interpreted as CachedAnalysis object
    last_cached_analysis: Optional[Any] = None
    landmarks_info: Optional[Any] = None

    def get_file_io(self):
        return ProjectFileIO(project=self)

    @property
    def subjects(self) -> Iterator[Subject]:
        return Subject.list(project=self)

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
        file_source: Path,
        segmentation: Segmentation,
        pre_cropping_source: Optional[Path] = None,
        pre_alignment_source: Optional[Path] = None,
    ) -> GroomedSegmentation:
        return GroomedSegmentation(
            file_source=file_source,
            segmentation=segmentation,
            project=self,
            pre_cropping_source=pre_cropping_source,
            pre_alignment_source=pre_alignment_source,
        ).create()

    def add_groomed_mesh(
        self,
        file_source: Path,
        mesh: Mesh,
        pre_cropping_source: Optional[Path] = None,
        pre_alignment_source: Optional[Path] = None,
    ) -> GroomedMesh:
        return GroomedMesh(
            file_source=file_source,
            mesh=mesh,
            project=self,
            pre_cropping_source=pre_cropping_source,
            pre_alignment_source=pre_alignment_source,
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

        if self.file:
            contents = json.load(open(str(self.file.path)))
            if 'landmarks' in contents:
                self.landmarks_info = contents['landmarks']

        result = super().create()
        if self.file:
            file_io.load_data()

        # Load the new dataset so we get an appropriate file field
        assert result.id
        return Project.from_id(result.id)

    def download(self, folder: Union[str, Path]):
        session = current_session()
        self.file.download(folder)
        r: requests.Response = session.get(f'{self._endpoint}/{self.id}/download/')
        raise_for_status(r)
        data = r.json()
        files = data['download_paths']
        print(f'Downloading {len(files)} files...')
        if len(files):
            print_progress_bar(0, len(files))
            for index, (path, url) in enumerate(files.items()):
                file_item: File = File(url)
                path_split = path.split('/')
                file_item.download(
                    Path(folder, *path_split[:-1]),
                    file_name=path_split[-1],
                )
                print_progress_bar(index + 1, len(files))
        session.close()
        print()


ProjectFileIO.update_forward_refs()
