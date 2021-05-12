from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable, Optional

import click
import requests
from swc_metadata.metadata import extract_metadata, validate_filename
import toml
from tqdm import tqdm
from xdg import BaseDirectory

if TYPE_CHECKING:
    from swcc.cli import CliContext
    from swcc.models import Dataset


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


def validate_dataset(ctx, src: Path, dataset: 'Dataset'):
    validated = True
    validated &= validate_files(ctx, Path(src / 'groomed'), dataset.groomed_pattern)
    validated &= validate_files(ctx, Path(src / 'segmentations'), dataset.segmentation_pattern)
    shape_models = Path(src / 'shape_models')
    for shape_model in os.listdir(shape_models):
        shape_model_path = Path(shape_models / shape_model)
        # All shape_models are stored in directories
        if not os.path.isdir(shape_model_path):
            click.echo(
                click.style(f'File {shape_model} found in {shape_models}', fg='red'),
                err=True,
            )
            validated = False
            continue

        # Check that all the auxiliary files are in place
        if 'analyze' not in os.listdir(shape_model_path):
            click.echo(
                click.style(f'File "analyze" not found in shape model {shape_model}', fg='red'),
                err=True,
            )
            validated = False
        if 'correspondence' not in os.listdir(shape_model_path):
            click.echo(
                click.style(
                    f'File "correspondence" not found in shape model {shape_model}', fg='red'
                ),
                err=True,
            )
            validated = False
        if 'transform' not in os.listdir(shape_model_path):
            click.echo(
                click.style(f'File "transform" not found in shape model {shape_model}', fg='red'),
                err=True,
            )
            validated = False
        for file in os.listdir(shape_model_path):
            if file not in ('analyze', 'correspondence', 'transform', 'particles'):
                click.echo(
                    click.style(
                        f'Unknown file "{file}" found in shape model {shape_model}', fg='red'
                    ),
                    err=True,
                )
                validated = False

        # Validate particles
        validated &= validate_files(
            ctx,
            Path(shape_model_path / 'particles'),
            dataset.particles_pattern,
        )

    return validated


def validate_files(ctx, path: Path, pattern: str):
    errors = []
    if os.path.exists(path):
        if os.path.isdir(path):
            for file in os.listdir(path):
                try:
                    validate_filename(pattern, file)
                except ValueError as e:
                    errors.append(e)
        else:
            errors.append(ValueError(f'{path} is not a directory'))
    else:
        errors.append(ValueError(f'{path} does not exist'))
    if errors:
        click.echo(click.style(f'Errors validating {path}:', fg='red'), err=True)
        for error in errors:
            click.echo(click.style(str(error), fg='red'), err=True)
    return errors == []


def files_to_upload(ctx: CliContext, existing: Iterable, path: Path) -> Iterable[Path]:
    existing_filenames = set([e.name for e in existing])
    for filename in os.listdir(path):
        if filename not in existing_filenames:
            yield Path(path / filename)


def upload_data_files(
    ctx: CliContext,
    existing: Iterable,
    path: Path,
    pattern: str,
    field: str,
    endpoint: str,
):
    for file_path in files_to_upload(ctx, existing, path):
        upload_data_file(ctx, file_path, pattern, field, endpoint)


def upload_data_file(
    ctx: CliContext,
    path: Path,
    pattern: str,
    field: str,
    endpoint: str,
):
    click.echo(f'uploading {path}')
    validate_filename(pattern, path.name)
    metadata = extract_metadata(pattern, path.name)
    with open(path, 'rb') as stream:
        response = ctx.s3ff.upload_file(stream, path.name, field)
        r = ctx.session.post(
            endpoint,
            json={**{'field_value': response['field_value']}, **metadata},
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
