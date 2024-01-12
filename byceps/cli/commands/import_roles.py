"""
byceps.cli.command.import_roles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Import roles and their assigned permissions from a TOML file.

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from pathlib import Path

import click
from flask.cli import with_appcontext

from byceps.services.authz import impex_service


_DEFAULT_DATA_FILE = Path('scripts') / 'data' / 'roles.toml'


@click.command()
@click.option(
    '-f',
    '--file',
    'data_file',
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=_DEFAULT_DATA_FILE,
)
@with_appcontext
def import_roles(data_file: Path) -> None:
    """Import authorization roles."""
    _import_roles(data_file)


def _import_roles(data_file: Path) -> None:
    click.echo('Importing roles ... ', nl=False)
    role_counts = impex_service.import_roles(data_file)
    click.secho('done. ', fg='green', nl=False)
    click.secho(
        f'Imported {role_counts.imported} roles, '
        f'skipped {role_counts.skipped} roles.',
    )
