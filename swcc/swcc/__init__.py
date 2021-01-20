from __future__ import annotations

from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
import logging
from pathlib import Path
import platform
import sys
import traceback

import click
from packaging.version import parse as parse_version
from pydantic import BaseModel
import requests
from requests.exceptions import RequestException
from requests_toolbelt.sessions import BaseUrlSession
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from .models import Dataset

FORMAT = '%(message)s'
logging.basicConfig(format=FORMAT, datefmt='[%X]', handlers=[RichHandler()])
logger = logging.getLogger(__name__)

try:
    __version__ = version('swcc')
except PackageNotFoundError:
    # package is not installed
    pass


class SwccSession(BaseUrlSession):
    page_size = 50

    def __init__(self, base_url: str):
        base_url = f'{base_url.rstrip("/")}/'  # tolerate input with or without trailing slash
        super().__init__(base_url=base_url)
        self.headers.update(
            {
                'User-agent': f'swcc/{__version__}',
                'Accept': 'application/json',
            }
        )


class CliContext(BaseModel):
    session: SwccSession
    url: str
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

    session = SwccSession(url)
    ctx.obj = CliContext(session=session, url=url.rstrip('/'), json_output=json_output)


@cli.group(name='dataset', short_help='get information about datasets')
@click.pass_obj
def dataset(ctx):
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


@dataset.command(name='list', help='list datasets')
@click.pass_obj
def list_(ctx):
    datasets = Dataset.list(ctx)

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


@dataset.command(name='download', help='download a dataset')
@click.argument('id_', type=int)
@click.argument('dest', type=click.Path(exists=False, file_okay=False, dir_okay=True))
@click.pass_obj
def download(ctx, id_: int, dest):
    dest = Path(dest)
    dest.mkdir(exist_ok=True)
    dataset = Dataset.from_id(ctx, id_)

    segmentations = Path(dest / 'segmentations')
    segmentations.mkdir(exist_ok=True, parents=True)
    for x in dataset.segmentations(ctx):
        x.download(ctx, segmentations)

    groomed = Path(dest / 'groomed')
    groomed.mkdir(exist_ok=True, parents=True)
    for x in dataset.groomed(ctx):
        x.download(ctx, groomed)

    shape_models = Path(dest / 'shape_models')
    shape_models.mkdir(exist_ok=True, parents=True)
    for x in dataset.shape_models(ctx):
        x.download(ctx, shape_models)

        particles = Path(shape_models / x.name / 'particles')
        particles.mkdir(exist_ok=True, parents=True)
        for particle in dataset.particles(ctx, x.id):
            particle.download(ctx, particles)


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


if __name__ == '__main__':
    main()
