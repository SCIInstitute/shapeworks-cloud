from __future__ import annotations

from datetime import datetime
import logging
import platform
import sys
import traceback

import click
from packaging.version import parse as parse_version
from pydantic import BaseModel
import requests
from requests.exceptions import RequestException

from . import SWCC_CONFIG_FILE, __version__
from .api import SwccSession
from .utils import get_config_value

logger = logging.getLogger(__name__)


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
