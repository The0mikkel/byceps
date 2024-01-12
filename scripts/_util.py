"""
byceps.scripts.util
~~~~~~~~~~~~~~~~~~~

Utilities for scripts

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from collections.abc import Callable

from byceps.application import create_cli_app


def call_with_app_context(func: Callable) -> None:
    """Call a callable inside of an application context."""
    app = create_cli_app()
    with app.app_context():
        func()
