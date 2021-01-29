from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
from typing import Any, Optional

import click
import requests
from shapeworks_cloud.core.metadata import extract_metadata, validate_filename
import toml
from tqdm import tqdm
from xdg import BaseDirectory


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


def upload_data_file(ctx, dataset, path, pattern, field, endpoint):
    click.echo(f'uploading {path}')
    validate_filename(pattern, path.name)
    metadata = extract_metadata(pattern, path.name)
    with open(path, 'rb') as stream:
        field = ctx.s3ff.upload_file(stream, path.name, field)
        r = ctx.session.post(
            endpoint,
            json={**{'field_value': field['field_value']}, **metadata},
        )
        r.raise_for_status()


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
