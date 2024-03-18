from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Union
from urllib.parse import unquote

from pydantic.v1 import AnyHttpUrl, FilePath, ValidationError, parse_obj_as
import requests

from ..api import current_session

logger = logging.getLogger(__name__)


class File:
    def __init__(self, v: Optional[Union[str, Path]], field_id: Optional[str] = None, **kwargs):
        self.field_id: Optional[str] = field_id
        self.path: Optional[Path] = None
        self.url: Optional[AnyHttpUrl] = None
        self.field_value: Optional[str] = None

        if v is not None:
            if isinstance(v, Path):
                self.path = v
            else:
                try:
                    self.path = parse_obj_as(FilePath, v)
                except ValidationError:
                    pass

                try:
                    self.url = parse_obj_as(AnyHttpUrl, v)
                except ValidationError:
                    pass

        if self.path is None and self.url is None:
            raise ValueError('Could not parse File as a local path or a remote url')

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
            raise Exception('Unknown field id, this is likely a bug in the File class')

        with self.path.open('rb') as f:
            logger.info('Uploading file %s', self.path.name)
            self.field_value = session.s3ff.upload_file(f, str(self.path.name), self.field_id)
            logger.debug('Uploaded file %s', self.path.name)

        return self.field_value

    def download(self, path: Union[str, Path], file_name=None) -> Path:
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

        if file_name:
            path = path / Path(file_name)
        else:
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
