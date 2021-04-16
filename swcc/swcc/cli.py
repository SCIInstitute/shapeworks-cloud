from __future__ import annotations

from datetime import datetime
import json
import logging
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

from . import SWCC_CONFIG_FILE, __version__
from .api import SwccSession
from .models import GroomedDataset, Optimization, Project
from .utils import get_config_value, update_config_value

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


@cli.group(name='groomed-dataset', short_help='get information about groomed datasets')
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


# @dataset.command(name='create', help='create a groomed dataset')
# @click.argument('name')
# @click.argument('segmentations', type=click_pathlib.Path(dir_okay=False, exists=True), nargs=-1)
# @click.pass_obj
# def create(ctx, name, segmentations):
#     dataset = GroomedDataset.create(ctx, name=name, segmentations=segmentations)
#     click.echo(json.dumps(dataset.dict(), indent=2, default=str))


@dataset.command(name='delete', help='delete a groomed dataset')
@click.argument('id_', type=int, metavar='id')
@click.pass_obj
def delete(ctx, id_):
    GroomedDataset.delete(ctx, id_)


@dataset.command(name='list', help='list groomed datasets')
@click.pass_obj
def list_(ctx):
    datasets = GroomedDataset.list(ctx)

    if ctx.json_output:
        for dataset in datasets:
            click.echo(dataset.json())
    else:
        console = Console()

        table = Table(show_header=True, header_style='bold green')
        table.add_column('ID')
        table.add_column('Created')
        table.add_column('Name', width=50)
        table.add_column('Segmentations')

        for dataset in datasets:
            table.add_row(
                f'{dataset.id}',
                dataset.created.strftime('%c'),
                dataset.name,
                f'{dataset.num_segmentations}',
            )

        console.print(table)


@cli.group(name='project', short_help='get information about projects')
@click.pass_obj
def project(ctx):
    pass


@project.command(name='create', help='create a project')
@click.argument('name')
@click.argument('groomed_dataset', type=int)
@click.pass_obj
def create_project(ctx, name, groomed_dataset):
    project = Project.create(ctx, name, groomed_dataset)
    click.echo(json.dumps(project.dict(), indent=2, default=str))


@cli.group(name='optimization', short_help='run optimizations and get results')
@click.pass_obj
def optimization(ctx):
    pass


@optimization.command(name='create', help='create an optimization run')
@click.argument('project', type=click.INT)
@click.option(
    '-n', '--number-of-particles', type=click.IntRange(min=1), default=128, show_default=True
)
@click.option('--use-normals', type=bool, default=False, show_default=True)
@click.option('--normal-weight', type=float, default=10, show_default=True)
@click.option(
    '--checkpointing-interval', type=click.IntRange(min=1), default=1000, show_default=True
)
@click.option('--iterations-per-split', type=click.IntRange(min=1), default=1000, show_default=True)
@click.option(
    '--optimization-iterations', type=click.IntRange(min=1), default=1000, show_default=True
)
@click.option('--starting-regularization', type=float, default=10, show_default=True)
@click.option('--ending-regularization', type=float, default=10, show_default=True)
@click.option('--recompute-regularization-interval', type=int, default=1, show_default=True)
@click.option('--relative-weighting', type=float, default=1, show_default=True)
@click.option('--initial-relative-weighting', type=float, default=1, show_default=True)
@click.option('--procrustes-interval', type=int, default=0, show_default=True)
@click.option('--procrustes-scaling', type=bool, default=False, show_default=True)
@click.pass_obj
def create_optimization(ctx, **kwargs):
    optimization = Optimization.create(ctx, **kwargs)
    click.echo(json.dumps(optimization.dict(), indent=2, default=str))


@cli.command(name='login', help='authenticate with shapeworks cloud')
@click.pass_obj
def login(ctx):
    while True:
        username = click.prompt('username', err=True)
        password = click.prompt('password', hide_input=True, err=True)

        # explicitly sidestep the session, since it checks for auth-related errors
        # to tell the user to login.
        r = requests.post(
            f'{ctx.url.rstrip("/").replace("/api/v1", "")}/api-token-auth/',
            data={'username': username, 'password': password},
        )

        if r.ok:
            update_config_value(SWCC_CONFIG_FILE, 'token', r.json()['token'])
            return click.echo(click.style('logged in successfully.', fg='green'), err=True)
        elif r.status_code == 400:
            continue
        else:
            # an error other than 'bad credentials'
            r.raise_for_status()


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
