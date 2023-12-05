import inspect
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Type, TypeVar, Union

from pydantic.v1 import AnyHttpUrl, BaseModel, PrivateAttr, parse_obj_as, validator
import requests

from ..api import current_session
from .file import File

ModelType = TypeVar('ModelType', bound='ApiModel')


class ApiModel(BaseModel):
    _endpoint: Optional[str] = None
    _file_fields: Dict = {}
    _files: Dict = PrivateAttr(default_factory=dict)

    id: Optional[int] = None

    @validator('*', pre=True)
    def fetch_entity(cls, v, field):
        type_ = cls.__fields__[field.name].type_
        if (
            inspect.isclass(type_)
            and type_ is not Any
            and issubclass(type_, ApiModel)
            and isinstance(v, int)
        ):
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
            cache[id] = json
        return cls.from_json(cache[id])

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
                yield cls.from_json(result)
            if not data.get('next'):
                return

            r = session.get(data['next'])

    @classmethod
    def from_json(cls: Type[ModelType], original_json, **kwargs):
        json = original_json.copy()
        for key, value in cls.__fields__.items():
            if key in kwargs:
                json[key] = kwargs[key]
            elif '_source' in key:
                new_key = key.replace('_source', '')
                json[key] = json[new_key]
                del json[new_key]
            elif (
                key in json
                and type(json[key]) == int
                and inspect.isclass(value.type_)  # exclude Unions of multiple classes
                and value.type_ is not Any
                and issubclass(value.type_, ApiModel)
            ):
                json[key] = value.type_.from_id(json[key])
        return cls(**json)

    def to_json(self):
        json = self.__dict__.copy()
        if 'file_io' in json:
            del json['file_io']
        for key, value in self:
            if '_source' in key:
                del json[key]
                new_key = key.replace('_source', '')
                file = getattr(self, new_key)
                if file is not None:
                    if file.field_value:
                        json[new_key] = file.field_value
                    else:
                        json[new_key] = file.upload()
            if isinstance(value, File):
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
        return json

    def delete(self) -> None:
        from .utils import raise_for_status

        session = current_session()

        self.assert_remote()
        r: requests.Response = session.delete(f'{self._endpoint}/{self.id}/')
        raise_for_status(r)
        self.id = None

    def create(self: ModelType) -> ModelType:
        from .utils import raise_for_status

        session = current_session()

        self.assert_local()
        json = self.to_json()
        r: requests.Response = session.post(f'{self._endpoint}/', json=json)
        raise_for_status(r)
        json = r.json()
        self.id = json['id']
        for key, file in self._files.items():
            if key in json:
                file.url = parse_obj_as(AnyHttpUrl, json[key])
        if 'creator' in r.json():
            self.creator = r.json()['creator']
        return self

    def download_files(self, path: Union[str, Path]) -> Iterator[Path]:
        for file in self._files.values():
            yield file.download(path)

    def assert_remote(self):
        if self.id is None:
            raise Exception('This entity has not yet been created on the server.')

    def assert_local(self):
        if self.id is not None:
            raise Exception('This entity already exists on the server (id: %r).' % self.id)

    def __getattribute__(self, name):
        if name != '_file_fields':
            if name in self._file_fields.keys():
                source = object.__getattribute__(self, name + '_source')
                if source is not None and name not in self._files:
                    self._files[name] = File(source, field_id=self._file_fields[name])
                return self._files.get(name)

        # Default behaviour
        return object.__getattribute__(self, name)
