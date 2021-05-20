from __future__ import annotations

from pathlib import Path
from typing import Generic, List, Literal, Optional, Type, TypeVar, Union, get_args

from pydantic import AnyHttpUrl, BaseModel, FilePath, StrictStr, ValidationError, parse_obj_as
from pydantic.fields import ModelField
from requests import Response

from .api import SwccSession
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

    def upload(self, session: SwccSession):
        if self.field_value:
            return self.field_value

        if self.url is not None or self.path is None:
            # trying to upload a file when the model was sourced from the server
            raise Exception('Cannot upload a remote file reference')

        if self.field_id is None:
            # I assume validate will always get called, but pydantic *might* be doing something
            # unusual in some cases.
            raise Exception('Unknown field id, this is likely a bug in teh FileType class')

        with self.path.open('rb') as f:
            self.field_value = session.s3ff.upload_file(f, self.path.name, self.field_id)[
                'field_value'
            ]

        return self.field_value


ModelType = TypeVar('ModelType', bound='ApiModel')


class ApiModel(BaseModel):
    _endpoint: str

    id: Optional[int]

    @classmethod
    def from_id(cls: Type[ModelType], session: SwccSession, id: int) -> ModelType:
        r: Response = session.get(f'{cls._endpoint}/{id}/')
        raise_for_status(r)
        json = r.json()
        for key, value in cls.__fields__.items():
            if issubclass(value.type_, ApiModel):
                json[key] = value.type_.from_id(session, json[key])
        return cls(**json)

    @classmethod
    def list(cls: Type[ModelType], session: SwccSession, **kwargs) -> List[ModelType]:
        r: Response = session.get(f'{cls._endpoint}/', json=kwargs)
        raise_for_status(r)
        return [cls(**obj) for obj in r.json()['results']]

    def delete(self, session: SwccSession) -> None:
        self.assert_remote()
        r: Response = session.delete(f'{self._endpoint}/{self.id}/')
        raise_for_status(r)
        self.id = None

    def create(self, session: SwccSession) -> None:
        self.assert_local()
        json = self.dict()
        for key, value in self:
            if isinstance(value, FileType):
                json[key] = value.upload(session)
            if isinstance(value, ApiModel):
                if value.id is None:
                    value.create(session)
                json[key] = value.id

        r: Response = session.post(f'{self._endpoint}/', json=json)
        raise_for_status(r)
        self.id = r.json()['id']

    def assert_remote(self):
        if self.id is None:
            raise Exception('This entity has not yet been created on the server.')

    def assert_local(self):
        if self.id is not None:
            raise Exception('This entity already exists on the server.')


class Dataset(ApiModel):
    _endpoint: str = 'datasets'

    name: NonEmptyString
    license: NonEmptyString
    description: NonEmptyString
    acknowledgement: NonEmptyString
    keywords: str = ''
    contributors: str = ''
    publications: str = ''


class Subject(ApiModel):
    _endpoint: str = 'subjects'

    name: NonEmptyString
    dataset: Dataset


class Segmentation(ApiModel):
    _endpoint: str = 'segmentations'

    file: FileType[Literal['core.Segmentation.file']]
    anatomy_type: NonEmptyString
    subject: Subject
