from __future__ import annotations

import itertools
from pathlib import Path, PurePath
from tempfile import TemporaryDirectory

try:
    from typing import Any, Dict, Iterator, Literal, Optional, Tuple, Union
except ImportError:
    from typing import (
        Any,
        Dict,
        Iterator,
        Optional,
        Tuple,
        Union,
    )
    from typing_extensions import (  # type: ignore
        Literal,
    )

from openpyxl import load_workbook
from pydantic import BaseModel

from .api_model import ApiModel
from .dataset import Dataset
from .file_type import FileType
from .other_models import GroomedMesh, GroomedSegmentation, Mesh, OptimizedShapeModel, Segmentation
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
        data = None
        if str(file).endswith('xlsx'):
            data, optimize = self.load_data_from_excel(file)
        elif str(file).endswith('json'):
            data, optimize = self.load_data_from_json(file)
        else:
            raise Exception(f'Unknown spreadsheet format in {file} - expected .xlsx or .json')
        if interpret and data is not None and optimize is not None:
            shape_model = self.interpret_optimize(optimize, file.parent)
            self.interpret_data(data, file.parent, shape_model)
        return data, optimize

    def load_data_from_excel(self, file):
        assert file  # should be guaranteed by assert_local
        xls = load_workbook(str(file), read_only=True)

        for sheet_name in ['data', 'optimize']:
            if sheet_name not in xls:
                raise Exception(f'`{sheet_name}` sheet not found')

        return xls['data'], xls['optimize']

    def load_data_from_json(self, file):
        return None, None

    def _iter_data_sheet(
        self, sheet: Any, root: Path
    ) -> Iterator[Tuple[Path, Path, str, Path, Path, Path]]:

        required = [
            'shape',
            'groomed',
            'alignment',
            'local_particles',
            'world_particles',
        ]
        optional = [
            'procrustes',
            'constraints',
        ]
        headers = next(sheet.values)
        if not any(all(k + suffix in headers for k in required) for suffix in ('_file', '_1')):
            raise Exception(
                'Unknown spreadsheet format - expected headers to include %r '
                'with a suffix of either _file or _1, found %r' % (required, headers)
            )
        for idx in itertools.count():
            suffix = '_file' if not idx else '_%d' % idx
            if not all(k + suffix in headers for k in required):
                if idx >= 1:
                    break
                continue
            col = {
                k: headers.index(k + suffix) for k in required + optional if k + suffix in headers
            }
            rows = sheet.values
            next(rows)  # skip header
            for rowrec in rows:
                row = {k: rowrec[col[k]] for k in col}
                if not row['shape']:
                    # It's possible to get XLSX files with empty rows where every column is None
                    continue

                shape_file = root / row['shape']
                groomed_file = (root / row['groomed']) if row['groomed'] else None
                local = (root / row['local_particles']) if row['local_particles'] else None
                world = (root / row['world_particles']) if row['world_particles'] else None
                alignment_file = row['alignment']
                constraints = (
                    (root / row['constraints'])
                    if 'constraints' in row and row['constraints']
                    else None
                )

                yield shape_file, groomed_file, alignment_file, local, world, constraints

    def interpret_optimize(self, data, root):
        expected = ('key', 'value')
        headers = next(data)
        if headers[: len(expected)] != expected:
            raise Exception(
                'Unknown spreadsheet format - expected headers to be %r, found %r'
                % (expected, headers[: len(expected)])
            )

        params: Dict[str, Union[str, float]] = {}
        for row in data:
            key, value = row
            try:
                value = float(value)
            except ValueError:
                pass
            params[key] = value

        return self.project.add_shape_model(params)

    def interpret_data(self, data, root, shape_model):
        segmentations = {
            PurePath(segmentation.file.name).stem: segmentation
            for segmentation in self.project.dataset.segmentations
        }
        meshes = {PurePath(mesh.file.name).stem: mesh for mesh in self.project.dataset.meshes}

        for (
            shape_file,
            groomed_file,
            alignment_file,
            local,
            world,
            constraints,
        ) in self._iter_data_sheet(data, root):
            groomed_segmentation = None
            groomed_mesh = None
            data_type = shape_file_type(shape_file)

            if groomed_file:
                if data_type == Segmentation:
                    segmentation = segmentations.get(shape_file.stem)
                    if not segmentation:
                        raise Exception(f'Could not find segmentation for "{shape_file}"')
                    groomed_segmentation = self.project.add_groomed_segmentation(
                        file=groomed_file,
                        segmentation=segmentation,
                    )
                elif data_type == Mesh:
                    mesh = meshes.get(shape_file.stem)
                    if not mesh:
                        raise Exception(f'Could not find mesh for "{shape_file}"')
                    groomed_mesh = self.project.add_groomed_mesh(
                        file=groomed_file,
                        mesh=mesh,
                    )

            if alignment_file and local and world:
                with TemporaryDirectory() as dir:
                    transform = Path(dir) / f'{shape_file.stem}.transform'
                    with transform.open('w') as f:
                        f.write(alignment_file)

                    shape_model.add_particles(
                        world=world,
                        local=local,
                        transform=transform,
                        groomed_segmentation=groomed_segmentation,
                        groomed_mesh=groomed_mesh,
                        constraints=constraints,
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
