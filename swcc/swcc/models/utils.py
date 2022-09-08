from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
import json
import logging
import os
from pathlib import Path
from typing import Any, Iterable, Optional

import click
from pydantic import StrictStr
import requests
import toml
from tqdm import tqdm
from xdg import BaseDirectory

from ..api import SwccSession

logger = logging.getLogger(__name__)


class FileIO(ABC):
    @abstractmethod
    def load_data(self, interpret=True):
        pass

    @abstractmethod
    def interpret_data(self, data, root):
        pass


class NonEmptyString(StrictStr):
    min_length = 1


def shape_file_type(path: Path):
    """
    Determine the type of the shape file.

    As described in https://github.com/SCIInstitute/ShapeWorks/blob/3344bbfd42cb83eea50d01c06218e3034b5c67aa/Libs/Mesh/Mesh.h#L212,
    Meshes are of file type "vtk", "vtp", "ply", "stl", "obj", while Segmentations are any other
    file type.
    """  # noqa: E501
    from .other_models import Mesh, Segmentation

    file_type = path.suffix
    if file_type in ['.vtk', '.vtp', '.ply', '.stl', '.obj']:
        return Mesh
    else:
        return Segmentation


def raise_for_status(response: requests.Response):
    try:
        response.raise_for_status()
    except requests.HTTPError:
        data = None
        try:
            data = json.dumps(response.json(), indent=2)
        except Exception:
            data = response.text

        if data:
            click.echo(click.style(f'Received:\n{data}\n', fg='yellow'), err=True)
        raise


def download_file(r: requests.Response, dest: Path, name: str, mtime: Optional[datetime] = None):
    filename = dest / name
    with tqdm.wrapattr(
        open(filename, 'wb'),
        'write',
        miniters=1,
        desc=str(filename),
        total=int(r.headers.get('content-length', 0)),
    ) as f:
        for chunk in r.iter_content(1024 * 1024 * 16):
            f.write(chunk)

    if mtime:
        os.utime(filename, (datetime.now().timestamp(), mtime.timestamp()))


def files_to_upload(session: SwccSession, existing: Iterable, path: Path) -> Iterable[Path]:
    existing_filenames = set([e.name for e in existing])
    for filename in os.listdir(path):
        if filename not in existing_filenames:
            yield Path(path / filename)


def upload_path(session: SwccSession, path: Path, field: str, name=None) -> str:
    if name is None:
        name = path.name
    with path.open('rb') as f:
        return session.s3ff.upload_file(f, name, field)


def update_config_value(filename: str, key: str, value: Any) -> None:
    from swcc import SWCC_CONFIG_PATH

    BaseDirectory.save_config_path(SWCC_CONFIG_PATH)

    config_dir = BaseDirectory.load_first_config(SWCC_CONFIG_PATH)
    config_file = os.path.join(config_dir, filename)

    if os.path.exists(config_file):
        with open(config_file, 'r') as infile:
            config = toml.load(infile)
            config['default'][key] = value
    else:
        config = {'default': {key: value}}

    with open(config_file, 'w') as outfile:
        toml.dump(config, outfile)


def get_config_value(filename: str, key: str) -> Optional[Any]:
    from swcc import SWCC_CONFIG_FILE, SWCC_CONFIG_PATH

    BaseDirectory.save_config_path(SWCC_CONFIG_PATH)
    config_dir: Optional[str] = BaseDirectory.load_first_config(SWCC_CONFIG_PATH)

    if config_dir:
        config_file = os.path.join(config_dir, SWCC_CONFIG_FILE)

        if os.path.exists(config_file):
            with open(config_file, 'r') as infile:
                config = toml.load(infile)['default']
                return config.get(key)

    return None
