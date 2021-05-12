from __future__ import annotations

from datetime import datetime
import logging
import os
from pathlib import Path
import platform
import sys
import traceback

import click
from packaging.version import parse as parse_version
from pydantic import BaseModel
import requests
from requests.exceptions import RequestException
from rich.console import Console
from rich.table import Table
from s3_file_field_client import S3FileFieldClient

from swcc.utils import files_to_upload, update_config_value, upload_data_files, validate_dataset

from . import SWCC_CONFIG_FILE, __version__
from .api import SwccSession
from .models import Dataset
from .utils import get_config_value

logger = logging.getLogger(__name__)


class CliContext(BaseModel):
    session: SwccSession
    url: str
    s3ff: S3FileFieldClient
    json_output: bool

    class Config:
        arbitrary_types_allowed = True


def newer_version_available():
    if __version__ is None:
        return False

    this_version = parse_version(__version__)
    if this_version.is_devrelease:
        return False

    r = requests.get('https://pypi.org/pypi/swcc/json', timeout=(5, 5))
    r.raise_for_status()
    releases = [parse_version(v) for v in r.json()['releases'].keys()]
    for release in releases:
        if not (release.is_prerelease or release.is_devrelease) and release > this_version:
            return True
    return False


def session_response_handler(r: requests.Response, *args, **kwargs):
    if r.status_code in [401, 403]:
        click.echo(
            click.style(
                "You are attempting to perform an authorized operation but you aren't logged in.\n"  # noqa
                "Run 'swcc login' to continue.",
                fg='yellow',
            ),
            err=True,
        )
        sys.exit(1)


@click.group()
@click.option('--url', default='https://app.shapeworks-cloud.org/api/v1', envvar='SWCC_URL')
@click.option('--json', 'json_output', is_flag=True)
@click.option('-v', '--verbose', count=True)
@click.version_option()
@click.pass_context
def cli(ctx, url, json_output: bool, verbose: int):
    if verbose >= 2:
        logger.setLevel(logging.DEBUG)
    elif verbose >= 1:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARN)

    try:
        if newer_version_available():
            click.echo(
                click.style(
                    """There is a newer version of swcc available.
You must upgrade to the latest version before continuing.
""",
                    fg='yellow',
                ),
                err=True,
            )
            click.echo(click.style('pip install --upgrade swcc', fg='green'), err=True)
            sys.exit(1)
    except RequestException:
        click.echo(click.style('Failed to check for newer version of swcc:', fg='red'), err=True)
        raise

    token = get_config_value(SWCC_CONFIG_FILE, 'token')
    session = SwccSession(url)
    if token:
        session.set_token(token)
    session.hooks['response'] = session_response_handler
    ctx.obj = CliContext(
        session=session,
        url=url.rstrip('/'),
        s3ff=S3FileFieldClient(url.rstrip('/') + '/s3-upload/', session),
        json_output=json_output,
    )


@cli.group(name='dataset', short_help='get information about datasets')
@click.pass_obj
def dataset(ctx: CliContext):
    pass


def formatted_size(size, base=1024, unit='B'):
    if size < base:
        return f'{size} {unit}'
    units = ['', 'K', 'M', 'G', 'T']
    i = 0
    while i < 5 and size >= base:
        size /= base
        i += 1
    return f'{size:.2f} {units[i]}{unit}'


@dataset.command(name='create', help='create a dataset')
@click.argument('name', type=str)
@click.argument('groomed-pattern', type=str)
@click.argument('segmentation-pattern', type=str)
@click.argument('particles-pattern', type=str)
@click.pass_obj
def create(ctx: CliContext, name, groomed_pattern, segmentation_pattern, particles_pattern):
    dataset = Dataset.create(
        ctx.session,
        name=name,
        groomed_pattern=groomed_pattern,
        segmentation_pattern=segmentation_pattern,
        particles_pattern=particles_pattern,
    )
    click.echo(dataset)


@dataset.command(name='list', help='list datasets')
@click.pass_obj
def list_(ctx: CliContext):
    datasets = Dataset.list(ctx.session)

    if ctx.json_output:
        for dataset in datasets:
            click.echo(dataset.json())
    else:
        console = Console()

        table = Table(show_header=True, header_style='bold green')
        table.add_column('ID')
        table.add_column('Created')
        table.add_column('Name', width=50)
        table.add_column('Size')
        table.add_column('Segmentations')
        table.add_column('Groomed')
        table.add_column('Shape Models')

        for dataset in datasets:
            table.add_row(
                f'{dataset.id}',
                dataset.created.strftime('%c'),
                dataset.name,
                f'{formatted_size(dataset.size)}',
                f'{dataset.num_segmentations}',
                f'{dataset.num_groomed}',
                f'{dataset.num_shape_models}',
            )

        console.print(table)


@dataset.command(name='delete', help='delete a dataset')
@click.argument('id_', type=int, metavar='ID')
@click.pass_obj
def delete(ctx: CliContext, id_: int):
    dataset = Dataset.from_id(ctx.session, id_)

    if click.confirm(
        f'Are you sure you want to delete the dataset "{dataset.name}"? This is irreversible.'
    ):
        Dataset.delete(ctx.session, id_)
        click.echo('deleted.')


@dataset.command(name='download', help='download a dataset')
@click.argument('id_', type=int, metavar='ID')
@click.argument('dest', type=click.Path(exists=False, file_okay=False, dir_okay=True))
@click.option('-s', '--subject-id', type=int, multiple=True)
@click.pass_obj
def download(ctx: CliContext, id_: int, dest, subject_id):
    dest = Path(dest)
    dest.mkdir(exist_ok=True)
    dataset = Dataset.from_id(ctx.session, id_)

    segmentations = Path(dest / 'segmentations')
    segmentations.mkdir(exist_ok=True, parents=True)
    for seg in dataset.segmentations(ctx.session):
        if (not subject_id) or (seg.subject in subject_id):
            seg.download(ctx.session, segmentations)

    groomed = Path(dest / 'groomed')
    groomed.mkdir(exist_ok=True, parents=True)
    for g in dataset.groomed(ctx.session):
        if (not subject_id) or (g.subject in subject_id):
            g.download(ctx.session, groomed)

    shape_models = Path(dest / 'shape_models')
    shape_models.mkdir(exist_ok=True, parents=True)
    for s in dataset.shape_models(ctx.session):
        s.download(ctx.session, shape_models)

        particles = Path(shape_models / s.name / 'particles')
        particles.mkdir(exist_ok=True, parents=True)
        for particle in dataset.particles(ctx.session, s.id):
            if (not subject_id) or (particle.subject in subject_id):
                particle.download(ctx.session, particles)


@dataset.command(name='validate', help='validate a dataset')
@click.argument('id_', type=int, metavar='ID')
@click.argument('src', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.pass_obj
def validate(ctx: CliContext, id_: int, src):
    src = Path(src)
    dataset = Dataset.from_id(ctx.session, id_)
    if validate_dataset(ctx, src, dataset):
        click.echo(click.style('validation succeeded', fg='green'))


@dataset.command(name='upload', help='upload a dataset')
@click.argument('id_', type=int, metavar='ID')
@click.argument('src', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.pass_obj
def upload(ctx: CliContext, id_: int, src):
    src = Path(src)
    dataset = Dataset.from_id(ctx.session, id_)

    if not validate_dataset(ctx, src, dataset):
        return

    upload_data_files(
        ctx,
        dataset.groomed(ctx.session),
        Path(src / 'groomed'),
        dataset.groomed_pattern,
        'core.Groomed.blob',
        f'datasets/{dataset.id}/groomed/',
    )

    upload_data_files(
        ctx,
        dataset.segmentations(ctx.session),
        Path(src / 'segmentations'),
        dataset.segmentation_pattern,
        'core.Segmentation.blob',
        f'datasets/{dataset.id}/segmentations/',
    )

    shape_models = Path(src / 'shape_models')
    existing_shape_models = list(dataset.shape_models(ctx.session))
    for shape_model_path in files_to_upload(ctx, existing_shape_models, shape_models):
        if os.path.isdir(shape_model_path):
            shape_model_data = {'name': shape_model_path.name, 'magic_number': 0}  # TODO
            for (filename, model_field, api_field) in [
                ('analyze', 'core.ShapeModel.analyze', 'analyze_field_value'),
                ('correspondence', 'core.ShapeModel.correspondence', 'correspondence_field_value'),
                ('transform', 'core.ShapeModel.transform', 'transform_field_value'),
            ]:
                with open(shape_model_path / filename, 'rb') as stream:
                    shape_model_data[api_field] = ctx.s3ff.upload_file(
                        stream, str(filename), model_field
                    )['field_value']

            r = ctx.session.post(f'datasets/{dataset.id}/shape_models/', data=shape_model_data)
            r.raise_for_status()

    # Update the list with any freshly created shape models
    existing_shape_models = list(dataset.shape_models(ctx.session))
    for shape_dir in os.listdir(shape_models):
        for shape_model in existing_shape_models:
            if shape_model.name == shape_dir:
                break
        else:
            # Shouldn't be possible, we just created any missing shape models
            raise ValueError(f'Shape model {shape_model.name} not found.')
        upload_data_files(
            ctx,
            dataset.particles(ctx.session, shape_model.id),
            Path(shape_models / shape_dir / 'particles'),
            dataset.particles_pattern,
            'core.Particles.blob',
            f'datasets/{dataset.id}/shape_models/{shape_model.id}/particles/',
        )


@cli.command(name='login', help='authenticate with shapeworks cloud')
@click.pass_obj
def login(ctx: CliContext):
    while True:
        username = click.prompt('username', err=True)
        password = click.prompt('password', hide_input=True, err=True)

        try:
            r = ctx.session.login(username, password)
        except Exception:
            click.echo(click.style('login failed', fg='red'), err=True)
            continue

        update_config_value(SWCC_CONFIG_FILE, 'token', r.json()['token'])
        return click.echo(click.style('logged in successfully.', fg='green'), err=True)


def main():
    try:
        cli()
    except Exception:
        click.echo(
            click.style(
                'The following unexpected error occurred while attempting your operation:\n',
                fg='red',
            ),
            err=True,
        )

        click.echo(traceback.format_exc(), err=True)

        click.echo(f'swcc:    v{__version__}', err=True)
        click.echo(f'python:  v{platform.python_version()}', err=True)
        click.echo(f'time:    {datetime.utcnow().isoformat()}', err=True)
        click.echo(f'os:      {platform.platform()}', err=True)
        click.echo(f'command: swcc {" ".join(sys.argv[1:])}\n', err=True)

        click.echo(
            click.style(
                'This is a bug in swcc and should be reported. You can open an issue below: ',
                fg='yellow',
            ),
            err=True,
        )
        click.echo(
            'https://github.com/girder/shapeworks-cloud/issues/new',
            err=True,
        )
