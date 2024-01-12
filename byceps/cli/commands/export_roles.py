"""
byceps.cli.command.export_roles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Export roles and their assigned permissions as TOML to STDOUT.

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

import click
from flask.cli import with_appcontext

from byceps.services.authz import impex_service


@click.command()
@with_appcontext
def export_roles() -> None:
    """Export authorization roles."""
    print(impex_service.export_roles())
