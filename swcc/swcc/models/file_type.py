from __future__ import annotations

import logging
from pathlib import Path

try:
    from typing import Generic, Optional, TypeVar, Union, get_args
except ImportError:
    from typing import (
        Generic,
        Optional,
        Union,
        TypeVar,
    )
    from typing_extensions import get_args

from urllib.parse import unquote

from pydantic import AnyHttpUrl, FilePath, ValidationError, parse_obj_as
from pydantic.fields import ModelField
import requests

from ..api import current_session

logger = logging.getLogger(__name__)
FieldId = TypeVar('FieldId', bound=str)


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
            logger.info('Uploading file %s', self.path.name)
            self.field_value = session.s3ff.upload_file(f, str(self.path.name), self.field_id)
            logger.debug('Uploaded file %s', self.path.name)

        return self.field_value

    def download(self, path: Union[Path, str]) -> Path:
        from .utils import raise_for_status

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

        logger.info('Downloading %s', path)
        with path.open('wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        self.path = path
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

    def __str__(self):
        return self.name
