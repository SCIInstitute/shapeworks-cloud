from __future__ import annotations

from pathlib import Path, PurePath
from tempfile import TemporaryDirectory
from typing import (
    Any,
    Dict,
    Generic,
    Iterator,
    Literal,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_args,
)
from urllib.parse import unquote

from openpyxl import load_workbook
from pydantic import (
    AnyHttpUrl,
    BaseModel,
    FilePath,
    StrictStr,
    ValidationError,
    parse_obj_as,
    validator,
)
from pydantic.fields import ModelField
import requests

from .api import current_session
from .utils import raise_for_status

FieldId = TypeVar('FieldId', bound=str)


class NonEmptyString(StrictStr):
    min_length = 1


class FileType(Generic[FieldId]):
    def __init__(
        self,
        path: Optional[Union[Path, str]] = None,
        url: Optional[str] = None,
        field_id: Optional[str] = None,
    ):
        self.field_id: Optional[str] = field_id
        self.path: Optional[Path] = None
        self.url: Optional[AnyHttpUrl] = None
        self.field_value: Optional[str] = None

        if path:
            self.path = parse_obj_as(FilePath, path)

        if url:
            self.url = parse_obj_as(AnyHttpUrl, url)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, field: ModelField, **kwargs):
        # this is probably a bad idea...
        if not field.sub_fields:
            raise SyntaxError('A field id must be provided when using FileType')

        field_id = get_args(field.sub_fields[0].type_)[0]
        if isinstance(v, FileType):
            v.field_id = field_id
            return v

        path = None
        url = None
        try:
            path = parse_obj_as(FilePath, v)
        except ValidationError:
            pass

        try:
            url = parse_obj_as(AnyHttpUrl, v)
        except ValidationError:
            pass

        if path is None and url is None:
            raise ValueError(f'Could not parse {v} as a local path or a remote url')

        return FileType(path=path, url=url, field_id=field_id)

    def upload(self):
        session = current_session()

        if self.field_value:
            return self.field_value

        if self.url is not None or self.path is None:
            # trying to upload a file when the model was sourced from the server
            raise Exception('Cannot upload a remote file reference')

        if self.field_id is None:
            # I assume validate will always get called, but pydantic *might* be doing something
            # unusual in some cases.
            raise Exception('Unknown field id, this is likely a bug in the FileType class')

        with self.path.open('rb') as f:
            self.field_value = session.s3ff.upload_file(f, self.path.name, self.field_id)[
                'field_value'
            ]

        return self.field_value

    def download(self, path: Union[Path, str]) -> Path:
        if self.url is None:
            raise Exception('Cannot download a local file')

        if not self.url.path:
            raise Exception('Server returned an unexpected url')

        path = Path(path)
        if path.is_file():
            raise ValueError('Expected a directory name')

        if not path.is_dir():
            path.mkdir(parents=True, exist_ok=True)

        path = path / self.url.path.split('/')[-1]
        r = requests.get(self.url, stream=True)
        raise_for_status(r)

        with path.open('wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return path

    @property
    def name(self) -> str:
        if self.path:
            return self.path.name
        elif self.url:
            if self.url.path is None:
                raise Exception('Invalid file url')
            return unquote(self.url.path.split('/')[-1])
        raise Exception('Invalid file object')


ModelType = TypeVar('ModelType', bound='ApiModel')


class ApiModel(BaseModel):
    _endpoint: str

    id: Optional[int]

    @validator('*', pre=True)
    def fetch_entity(cls, v, field: ModelField):
        type_ = cls.__fields__[field.name].type_
        if type_ is not Any and issubclass(type_, ApiModel) and isinstance(v, int):
            return type_.from_id(v)
        return v

    @classmethod
    def from_id(cls: Type[ModelType], id: int, **kwargs) -> ModelType:
        session = current_session()
        cache = session.cache[cls]

        if id not in cache:
            r: requests.Response = session.get(f'{cls._endpoint}/{id}/')
            raise_for_status(r)
            json = r.json()
            for key, value in cls.__fields__.items():
                if key in kwargs:
                    json[key] = kwargs[key]
                elif value.type_ is not Any and issubclass(value.type_, ApiModel):
                    json[key] = value.type_.from_id(json[key])
            cache[id] = cls(**json)
        return cache[id]

    @classmethod
    def list(cls: Type[ModelType], **kwargs) -> Iterator[ModelType]:
        session = current_session()

        filter: Dict[str, Any] = {}
        replace: Dict[str, ApiModel] = {}
        for key, value in kwargs.items():
            if isinstance(value, ApiModel):
                filter[key] = value.id
                replace[key] = value
            else:
                filter[key] = value

        r: requests.Response = session.get(f'{cls._endpoint}/', params=filter)

        while True:
            raise_for_status(r)
            data = r.json()
            for result in data['results']:
                result.update(replace)
                yield cls(**result)
            if not data.get('next'):
                return

            r = session.get(data['next'])

    def delete(self) -> None:
        session = current_session()

        self.assert_remote()
        r: requests.Response = session.delete(f'{self._endpoint}/{self.id}/')
        raise_for_status(r)
        self.id = None

    def create(self: ModelType) -> ModelType:
        session = current_session()

        self.assert_local()
        json = self.dict()
        for key, value in self:
            if isinstance(value, FileType):
                json[key] = value.upload()
            if isinstance(value, ApiModel):
                if value.id is None:
                    value.create()
                json[key] = value.id

        r: requests.Response = session.post(f'{self._endpoint}/', json=json)
        raise_for_status(r)
        self.id = r.json()['id']
        return self

    def download_files(self, path: Union[Path, str]) -> Iterator[Path]:
        for _, value in self:
            if isinstance(value, FileType):
                yield value.download(path)

    def assert_remote(self):
        if self.id is None:
            raise Exception('This entity has not yet been created on the server.')

    def assert_local(self):
        if self.id is not None:
            raise Exception('This entity already exists on the server (id: %r).' % self.id)


class Dataset(ApiModel):
    _endpoint = 'datasets'

    name: NonEmptyString
    license: NonEmptyString
    description: NonEmptyString
    acknowledgement: NonEmptyString
    keywords: str = ''
    contributors: str = ''
    publications: str = ''

    @property
    def subjects(self) -> Iterator[Subject]:
        self.assert_remote()
        return Subject.list(dataset=self)

    def add_subject(self, name: str) -> Subject:
        return Subject(name=name, dataset=self).create()

    @property
    def projects(self) -> Iterator[Project]:
        self.assert_remote()
        return Project.list(dataset=self)

    @property
    def segmentations(self) -> Iterator[Segmentation]:
        for subject in self.subjects:
            for segmentation in subject.segmentations:
                yield segmentation

    def add_project(self, file: Path, keywords: str = '', description: str = '') -> Project:
        project = Project(
            file=file,
            keywords=keywords,
            description=description,
            dataset=self,
        ).create()
        return project.load_project_spreadsheet()

    @classmethod
    def from_name(cls, name: str) -> Optional[Dataset]:
        results = cls.list(name=name)
        try:
            return next(results)
        except StopIteration:
            return None

    def load_data_spreadsheet(self, file: Union[Path, str]) -> Dataset:
        file = Path(file)
        xls = load_workbook(str(file), read_only=True)
        if 'data' not in xls:
            raise Exception('`data` sheet not found')

        data = xls['data'].values

        expected = ('shape_file',)
        headers = next(data)
        if headers[: len(expected)] != expected:
            raise Exception(
                'Unknown spreadsheet format in %r - expected headers to be %r, found %r'
                % (file, expected, headers[: len(expected)])
            )

        root = file.parent
        subjects: Dict[str, Subject] = {}

        for row in data:
            shape_file = root / row[0]
            if not shape_file.exists():
                raise Exception(f'Could not find shape file at "{shape_file}"')

            subject_name = shape_file.stem
            if subject_name not in subjects:
                subjects[subject_name] = self.add_subject(subject_name)

            subject = subjects[subject_name]

            # TODO: where to find the anatomy type?
            subject.add_segmentation(file=shape_file, anatomy_type='unknown')

        return self

    def download(self, path: Union[Path, str]):
        self.assert_remote()
        path = Path(path)
        for segmentation in self.segmentations:
            # TODO: add a dataset spreadsheet to the data model and get the path from it
            segmentation.file.download(path / 'segmentations')

        for project in self.projects:
            project.download(path)


class Subject(ApiModel):
    _endpoint = 'subjects'

    name: NonEmptyString
    dataset: Dataset

    @property
    def segmentations(self) -> Iterator[Segmentation]:
        self.assert_remote()
        return Segmentation.list(subject=self)

    def add_segmentation(self, file: Path, anatomy_type: str) -> Segmentation:
        return Segmentation(file=file, anatomy_type=anatomy_type, subject=self).create()


class Segmentation(ApiModel):
    _endpoint = 'segmentations'

    file: FileType[Literal['core.Segmentation.file']]
    anatomy_type: NonEmptyString
    subject: Subject


class Project(ApiModel):
    _endpoint = 'projects'

    file: FileType[Literal['core.Project.file']]
    keywords: str = ''
    description: str = ''
    dataset: Dataset

    @property
    def groomed_segmentations(self) -> Iterator[GroomedSegmentation]:
        self.assert_remote()
        return GroomedSegmentation.list(project=self)

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

    @property
    def shape_models(self) -> Iterator[OptimizedShapeModel]:
        self.assert_remote()
        return OptimizedShapeModel.list(project=self)

    def add_shape_model(self, parameters: Dict[str, Any]) -> OptimizedShapeModel:
        return OptimizedShapeModel(
            project=self,
            parameters=parameters,
        ).create()

    def load_project_spreadsheet(self) -> Project:
        file = self.file.path
        assert file  # should be guaranteed by assert_local

        root = file.parent
        xls = load_workbook(str(file), read_only=True)

        segmentations = {
            PurePath(segmentation.file.name).stem: segmentation
            for segmentation in self.dataset.segmentations
        }

        if 'optimize' not in xls or 'data' not in xls:
            raise Exception('`data` sheet not found')

        shape_model = self._parse_optimize_sheet(xls['optimize'].values)
        self._parse_data_sheet(segmentations, shape_model, xls['data'].values, root)

        return self

    def _iter_data_sheet(
        self, sheet: Any, root: Path
    ) -> Iterator[Tuple[Path, Path, str, Path, Path]]:
        expected = (
            'shape_file',
            'groomed_file',
            'alignment_file',
            'local_particles_file',
            'world_particles_file',
        )
        headers = next(sheet)
        if headers[: len(expected)] != expected:
            raise Exception(
                'Unknown spreadsheet format - expected headers to be %r, found %r'
                % (expected, headers[: len(expected)])
            )

        for row in sheet:
            shape_file, groomed_file, alignment_file, local, world = row

            shape_file = root / shape_file
            groomed_file = root / groomed_file
            local = root / local
            world = root / world

            yield shape_file, groomed_file, alignment_file, local, world

    def _parse_optimize_sheet(self, sheet: Any) -> OptimizedShapeModel:
        expected = ('key', 'value')
        headers = next(sheet)
        if headers[: len(expected)] != expected:
            raise Exception(
                'Unknown spreadsheet format - expected headers to be %r, found %r'
                % (expected, headers[: len(expected)])
            )

        params: Dict[str, Union[str, float]] = {}
        for row in sheet:
            key, value = row
            try:
                value = float(value)
            except ValueError:
                pass
            params[key] = value

        return self.add_shape_model(params)

    def _parse_data_sheet(
        self,
        segmentations: Dict[str, Segmentation],
        shape_model: OptimizedShapeModel,
        sheet: Any,
        root: Path,
    ):
        for shape_file, groomed_file, alignment_file, local, world in self._iter_data_sheet(
            sheet, root
        ):
            segmentation = segmentations.get(shape_file.stem)
            if not segmentation:
                raise Exception(f'Could not find segmentation for "{shape_file}"')

            groomed_segmentation = self.add_groomed_segmentation(
                file=groomed_file,
                segmentation=segmentation,
            )
            with TemporaryDirectory() as dir:
                transform = Path(dir) / f'{shape_file.stem}.transform'
                with transform.open('w') as f:
                    f.write(alignment_file)

                shape_model.add_particles(
                    world=world,
                    local=local,
                    transform=transform,
                    groomed_segmentation=groomed_segmentation,
                )

    def download(self, path: Union[Path, str]):
        path = Path(path)
        project_file = self.file.download(path)
        xls = load_workbook(str(project_file), read_only=True)
        sheet = xls['data'].values

        shape_model = next(self.shape_models)
        groomed_segmentations = {
            PurePath(gs.file.name).stem: gs for gs in self.groomed_segmentations
        }
        local_files = {PurePath(p.local.name).stem: p for p in shape_model.particles}

        # TODO: Do we detect if alignment_file (transform) is a path?
        for _, groomed_file, _, local, world in self._iter_data_sheet(sheet, path):
            gs = groomed_segmentations[groomed_file.stem]
            gs.file.download(groomed_file.parent)

            particles = local_files[local.stem]
            particles.local.download(local.parent)
            particles.world.download(world.parent)


class GroomedSegmentation(ApiModel):
    _endpoint = 'groomed-segmentations'

    file: FileType[Literal['core.GroomedSegmentation.file']]
    pre_cropping: Optional[FileType[Literal['core.GroomedSegmentation.pre_cropping']]] = None
    pre_alignment: Optional[FileType[Literal['core.GroomedSegmentation.pre_alignment']]] = None

    segmentation: Segmentation
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
        groomed_segmentation: GroomedSegmentation,
    ) -> OptimizedParticles:
        return OptimizedParticles(
            world=world,
            local=local,
            transform=transform,
            shape_model=self,
            groomed_segmentation=groomed_segmentation,
        ).create()


class OptimizedParticles(ApiModel):
    _endpoint = 'optimized-particles'

    world: FileType[Literal['core.OptimizedParticles.world']]
    local: FileType[Literal['core.OptimizedParticles.local']]
    transform: FileType[Literal['core.OptimizedParticles.transform']]
    shape_model: OptimizedShapeModel
    groomed_segmentation: GroomedSegmentation


class OptimizedPCAModel(ApiModel):
    _endpoint = 'optimized-pca-model'

    mean_particles: FileType[Literal['core.OptimizedPCAModel.mean_particles']]
    pca_modes: FileType[Literal['core.OptimizedPCAModel.pca_modes']]
    eigen_spectrum: FileType[Literal['core.OptimizedPCAModel.eigen_spectrum']]
    shape_model: OptimizedShapeModel
