from pathlib import Path

try:
    from typing import Any, Dict, Iterator, Optional, Type, TypeVar, Union
except ImportError:
    from typing import (
        Any,
        Dict,
        Iterator,
        Optional,
        Type,
        TypeVar,
        Union,
    )

from pydantic import BaseModel, validator
from pydantic.fields import ModelField
import requests

from ..api import current_session

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
        from .utils import raise_for_status

        session = current_session()
        cache = session.cache[cls]

        if id not in cache:
            r: requests.Response = session.get(f'{cls._endpoint}/{id}/')
            raise_for_status(r)
            json = r.json()
            for key, value in cls.__fields__.items():
                if key in kwargs:
                    json[key] = kwargs[key]
                elif json[key] and value.type_ is not Any and issubclass(value.type_, ApiModel):
                    json[key] = value.type_.from_id(json[key])
            cache[id] = cls(**json)
        return cache[id]

    @classmethod
    def list(cls: Type[ModelType], **kwargs) -> Iterator[ModelType]:
        from .utils import raise_for_status

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
        from .utils import raise_for_status

        session = current_session()

        self.assert_remote()
        r: requests.Response = session.delete(f'{self._endpoint}/{self.id}/')
        raise_for_status(r)
        self.id = None

    def create(self: ModelType) -> ModelType:
        from .file_type import FileType
        from .utils import raise_for_status

        session = current_session()

        self.assert_local()
        json = self.__dict__.copy()
        if 'file_io' in json:
            del json['file_io']
        for key, value in self:
            if isinstance(value, FileType):
                json[key] = value.upload()
            if isinstance(value, ApiModel):
                if value.id is None:
                    value.create()
                json[key] = value.id
            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], ApiModel):
                ids = []
                for item in value:
                    if item.id is None:
                        ids.append(item.create().id)
                    else:
                        ids.append(item.id)
                json[key] = ids

        r: requests.Response = session.post(f'{self._endpoint}/', json=json)
        raise_for_status(r)
        self.id = r.json()['id']
        return self

    def download_files(self, path: Union[Path, str]) -> Iterator[Path]:
        from .file_type import FileType

        for _, value in self:
            if isinstance(value, FileType):
                yield value.download(path)

    def assert_remote(self):
        if self.id is None:
            raise Exception('This entity has not yet been created on the server.')

    def assert_local(self):
        if self.id is not None:
            raise Exception('This entity already exists on the server (id: %r).' % self.id)
