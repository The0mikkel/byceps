#!/usr/bin/env python

"""Copy a snippet (in its latest version) from one site to another.

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

import click

from byceps.services.snippet import snippet_service
from byceps.services.snippet.errors import (
    SnippetAlreadyExistsError,
    SnippetNotFoundError,
)
from byceps.services.snippet.models import SnippetScope
from byceps.util.result import Err, Ok

from _util import call_with_app_context
from _validators import validate_site


@click.command()
@click.pass_context
@click.argument('source_site', callback=validate_site)
@click.argument('target_site', callback=validate_site)
@click.argument('language_code')
@click.argument('snippet_names', nargs=-1, required=True)
def execute(
    ctx, source_site, target_site, language_code: str, snippet_names
) -> None:
    source_scope = SnippetScope.for_site(source_site.id)
    target_scope = SnippetScope.for_site(target_site.id)

    for name in snippet_names:
        copy_snippet(source_scope, target_scope, name, language_code, ctx)

    click.secho('Done.', fg='green')


def copy_snippet(
    source_scope: SnippetScope,
    target_scope: SnippetScope,
    name: str,
    language_code: str,
    ctx,
) -> None:
    match snippet_service.copy_snippet(
        source_scope, target_scope, name, language_code
    ):
        case Ok(_):
            click.secho(
                f'Copied snippet "{name}" ({language_code}) '
                f'from scope "{source_scope.as_string()}" '
                f'to "{target_scope.as_string()}".',
                fg='green',
            )
        case Err(SnippetNotFoundError()):
            click.secho(
                f'Snippet "{name}" ({language_code}) not found '
                f'in scope "{source_scope.as_string()}".',
                fg='red',
            )
        case Err(SnippetAlreadyExistsError()):
            click.secho(
                f'Snippet "{name}" ({language_code}) already exists '
                f'in scope "{target_scope.as_string()}".',
                fg='red',
            )


if __name__ == '__main__':
    call_with_app_context(execute)
