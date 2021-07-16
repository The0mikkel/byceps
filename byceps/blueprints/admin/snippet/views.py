"""
byceps.blueprints.admin.snippet.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2021 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from typing import Optional
from flask import abort, g, request, url_for
from flask_babel import gettext

from ....services.snippet.dbmodels.snippet import (
    SnippetVersion as DbSnippetVersion,
)
from ....services.snippet import service as snippet_service
from ....services.snippet.transfer.models import Scope, SnippetVersionID
from ....services.text_diff import service as text_diff_service
from ....services.user import service as user_service
from ....signals import snippet as snippet_signals
from ....util.authorization import register_permission_enum
from ....util.datetime.format import format_datetime_short
from ....util.framework.blueprint import create_blueprint
from ....util.framework.flash import flash_error, flash_success
from ....util.framework.templating import templated
from ....util.iterables import pairwise
from ....util.views import (
    permission_required,
    redirect_to,
    respond_no_content_with_location,
)

from ...site.snippet.templating import get_snippet_context

from .authorization import SnippetPermission
from .forms import (
    DocumentCreateForm,
    DocumentUpdateForm,
    FragmentCreateForm,
    FragmentUpdateForm,
)
from .helpers import (
    find_brand_for_scope,
    find_site_for_scope,
    find_snippet_by_id,
)


blueprint = create_blueprint('snippet_admin', __name__)


register_permission_enum(SnippetPermission)


@blueprint.get('/for_scope/<scope_type>/<scope_name>')
@permission_required(SnippetPermission.view)
@templated
def index_for_scope(scope_type, scope_name):
    """List snippets for that scope."""
    scope = Scope(scope_type, scope_name)

    snippets = snippet_service.get_snippets_for_scope_with_current_versions(
        scope
    )

    user_ids = {snippet.current_version.creator_id for snippet in snippets}
    users = user_service.find_users(user_ids, include_avatars=True)
    users_by_id = user_service.index_users_by_id(users)

    brand = find_brand_for_scope(scope)
    site = find_site_for_scope(scope)

    return {
        'scope': scope,
        'snippets': snippets,
        'users_by_id': users_by_id,
        'brand': brand,
        'site': site,
    }


@blueprint.get('/snippets/<uuid:snippet_id>/current_version')
@permission_required(SnippetPermission.view)
def view_current_version(snippet_id):
    """Show the current version of the snippet."""
    snippet = find_snippet_by_id(snippet_id)

    version = snippet.current_version

    return view_version(version.id)


@blueprint.get('/versions/<uuid:snippet_version_id>')
@permission_required(SnippetPermission.view_history)
@templated
def view_version(snippet_version_id):
    """Show the snippet with the given id."""
    version = _find_version(snippet_version_id)

    snippet = version.snippet
    scope = snippet.scope
    creator = user_service.get_user(version.creator_id, include_avatar=True)
    is_current_version = version.id == snippet.current_version.id

    context = {
        'version': version,
        'scope': scope,
        'creator': creator,
        'brand': find_brand_for_scope(scope),
        'site': find_site_for_scope(scope),
        'is_current_version': is_current_version,
    }

    try:
        snippet_context = get_snippet_context(version)

        extra_context = {
            'snippet_title': snippet_context['page_title'],
            'snippet_head': snippet_context['head'],
            'snippet_body': snippet_context['body'],
            'error_occurred': False,
        }
    except Exception as e:
        extra_context = {
            'error_occurred': True,
            'error_message': str(e),
        }

    context.update(extra_context)

    return context


@blueprint.get('/snippets/<uuid:snippet_id>/history')
@permission_required(SnippetPermission.view_history)
@templated
def history(snippet_id):
    snippet = find_snippet_by_id(snippet_id)

    scope = snippet.scope

    versions = snippet_service.get_versions(snippet.id)
    versions_pairwise = list(pairwise(versions + [None]))

    user_ids = {version.creator_id for version in versions}
    users = user_service.find_users(user_ids, include_avatars=True)
    users_by_id = user_service.index_users_by_id(users)

    brand = find_brand_for_scope(scope)
    site = find_site_for_scope(scope)

    return {
        'scope': scope,
        'snippet': snippet,
        'versions_pairwise': versions_pairwise,
        'users_by_id': users_by_id,
        'brand': brand,
        'site': site,
    }


# -------------------------------------------------------------------- #
# document


@blueprint.get('/for_scope/<scope_type>/<scope_name>/documents/create')
@permission_required(SnippetPermission.create)
@templated
def create_document_form(scope_type, scope_name):
    """Show form to create a document."""
    scope = Scope(scope_type, scope_name)

    form = DocumentCreateForm()

    brand = find_brand_for_scope(scope)
    site = find_site_for_scope(scope)

    return {
        'scope': scope,
        'form': form,
        'brand': brand,
        'site': site,
    }


@blueprint.post('/for_scope/<scope_type>/<scope_name>/documents')
@permission_required(SnippetPermission.create)
def create_document(scope_type, scope_name):
    """Create a document."""
    scope = Scope(scope_type, scope_name)

    form = DocumentCreateForm(request.form)

    name = form.name.data.strip().lower()
    creator = g.user
    title = form.title.data.strip()
    head = form.head.data.strip()
    body = form.body.data.strip()
    image_url_path = form.image_url_path.data.strip()

    version, event = snippet_service.create_document(
        scope,
        name,
        creator.id,
        title,
        body,
        head=head,
        image_url_path=image_url_path,
    )

    flash_success(
        gettext(
            'Document "%(name)s" has been created.', name=version.snippet.name
        )
    )

    snippet_signals.snippet_created.send(None, event=event)

    return redirect_to('.view_version', snippet_version_id=version.id)


@blueprint.get('/documents/<uuid:snippet_id>/update')
@permission_required(SnippetPermission.update)
@templated
def update_document_form(snippet_id):
    """Show form to update a document."""
    snippet = find_snippet_by_id(snippet_id)
    current_version = snippet.current_version

    scope = snippet.scope

    form = DocumentUpdateForm(obj=current_version, name=snippet.name)

    brand = find_brand_for_scope(scope)
    site = find_site_for_scope(scope)

    return {
        'scope': scope,
        'form': form,
        'snippet': snippet,
        'brand': brand,
        'site': site,
    }


@blueprint.post('/documents/<uuid:snippet_id>')
@permission_required(SnippetPermission.update)
def update_document(snippet_id):
    """Update a document."""
    form = DocumentUpdateForm(request.form)

    snippet = find_snippet_by_id(snippet_id)

    creator = g.user
    title = form.title.data.strip()
    head = form.head.data.strip()
    body = form.body.data.strip()
    image_url_path = form.image_url_path.data.strip()

    version, event = snippet_service.update_document(
        snippet.id,
        creator.id,
        title,
        body,
        head=head,
        image_url_path=image_url_path,
    )

    flash_success(
        gettext(
            'Document "%(name)s" has been updated.',
            name=version.snippet.name,
        )
    )

    snippet_signals.snippet_updated.send(None, event=event)

    return redirect_to('.view_version', snippet_version_id=version.id)


@blueprint.get(
    '/documents/<uuid:from_version_id>/compare_to/<uuid:to_version_id>'
)
@permission_required(SnippetPermission.view_history)
@templated
def compare_documents(from_version_id, to_version_id):
    """Show the difference between two document versions."""
    from_version = _find_version(from_version_id)
    to_version = _find_version(to_version_id)

    snippet = from_version.snippet
    scope = snippet.scope

    if from_version.snippet_id != to_version.snippet_id:
        abort(400, 'The versions do not belong to the same snippet.')

    html_diff_title = _create_html_diff(from_version, to_version, 'title')
    html_diff_head = _create_html_diff(from_version, to_version, 'head')
    html_diff_body = _create_html_diff(from_version, to_version, 'body')
    html_diff_image_url_path = _create_html_diff(
        from_version, to_version, 'image_url_path'
    )

    brand = find_brand_for_scope(scope)
    site = find_site_for_scope(scope)

    return {
        'snippet': snippet,
        'scope': scope,
        'diff_title': html_diff_title,
        'diff_head': html_diff_head,
        'diff_body': html_diff_body,
        'diff_image_url_path': html_diff_image_url_path,
        'brand': brand,
        'site': site,
    }


# -------------------------------------------------------------------- #
# fragment


@blueprint.get('/for_scope/<scope_type>/<scope_name>/fragments/create')
@permission_required(SnippetPermission.create)
@templated
def create_fragment_form(scope_type, scope_name):
    """Show form to create a fragment."""
    scope = Scope(scope_type, scope_name)

    form = FragmentCreateForm()

    brand = find_brand_for_scope(scope)
    site = find_site_for_scope(scope)

    return {
        'scope': scope,
        'form': form,
        'brand': brand,
        'site': site,
    }


@blueprint.post('/for_scope/<scope_type>/<scope_name>/fragments')
@permission_required(SnippetPermission.create)
def create_fragment(scope_type, scope_name):
    """Create a fragment."""
    scope = Scope(scope_type, scope_name)

    form = FragmentCreateForm(request.form)

    name = form.name.data.strip().lower()
    creator = g.user
    body = form.body.data.strip()

    version, event = snippet_service.create_fragment(
        scope, name, creator.id, body
    )

    flash_success(
        gettext(
            'Fragment "%(name)s" has been created.', name=version.snippet.name
        )
    )

    snippet_signals.snippet_created.send(None, event=event)

    return redirect_to('.view_version', snippet_version_id=version.id)


@blueprint.get('/fragments/<uuid:snippet_id>/update')
@permission_required(SnippetPermission.update)
@templated
def update_fragment_form(snippet_id):
    """Show form to update a fragment."""
    snippet = find_snippet_by_id(snippet_id)
    current_version = snippet.current_version

    scope = snippet.scope

    form = FragmentUpdateForm(obj=current_version, name=snippet.name)

    brand = find_brand_for_scope(scope)
    site = find_site_for_scope(scope)

    return {
        'scope': scope,
        'form': form,
        'snippet': snippet,
        'brand': brand,
        'site': site,
    }


@blueprint.post('/fragments/<uuid:snippet_id>')
@permission_required(SnippetPermission.update)
def update_fragment(snippet_id):
    """Update a fragment."""
    form = FragmentUpdateForm(request.form)

    snippet = find_snippet_by_id(snippet_id)

    creator = g.user
    body = form.body.data.strip()

    version, event = snippet_service.update_fragment(
        snippet.id, creator.id, body
    )

    flash_success(
        gettext(
            'Fragment "%(name)s" has been updated.',
            name=version.snippet.name,
        )
    )

    snippet_signals.snippet_updated.send(None, event=event)

    return redirect_to('.view_version', snippet_version_id=version.id)


@blueprint.get(
    '/fragments/<uuid:from_version_id>/compare_to/<uuid:to_version_id>'
)
@permission_required(SnippetPermission.view_history)
@templated
def compare_fragments(from_version_id, to_version_id):
    """Show the difference between two fragment versions."""
    from_version = _find_version(from_version_id)
    to_version = _find_version(to_version_id)

    snippet = from_version.snippet
    scope = snippet.scope

    if from_version.snippet_id != to_version.snippet_id:
        abort(400, 'The versions do not belong to the same snippet.')

    html_diff_body = _create_html_diff(from_version, to_version, 'body')

    brand = find_brand_for_scope(scope)
    site = find_site_for_scope(scope)

    return {
        'snippet': snippet,
        'scope': scope,
        'diff_body': html_diff_body,
        'brand': brand,
        'site': site,
    }


# -------------------------------------------------------------------- #
# delete


@blueprint.delete('/snippets/<uuid:snippet_id>')
@permission_required(SnippetPermission.delete)
@respond_no_content_with_location
def delete_snippet(snippet_id):
    """Delete a snippet."""
    snippet = find_snippet_by_id(snippet_id)

    snippet_name = snippet.name
    scope = snippet.scope

    success, event = snippet_service.delete_snippet(
        snippet.id, initiator_id=g.user.id
    )

    if not success:
        flash_error(
            gettext(
                'Snippet "%(snippet_name)s" could not be deleted. Is it still mounted?',
                snippet_name=snippet_name,
            )
        )
        return url_for('.view_current_version', snippet_id=snippet.id)

    flash_success(
        gettext('Snippet "%(name)s" has been deleted.', name=snippet_name)
    )
    snippet_signals.snippet_deleted.send(None, event=event)
    return url_for(
        '.index_for_scope', scope_type=scope.type_, scope_name=scope.name
    )


# -------------------------------------------------------------------- #
# helpers


def _find_version(version_id: SnippetVersionID) -> DbSnippetVersion:
    version = snippet_service.find_snippet_version(version_id)

    if version is None:
        abort(404)

    return version


def _create_html_diff(
    from_version: DbSnippetVersion,
    to_version: DbSnippetVersion,
    attribute_name: str,
) -> Optional[str]:
    """Create an HTML diff between the named attribute's value of each
    of the two versions.
    """
    from_description = format_datetime_short(from_version.created_at)
    to_description = format_datetime_short(to_version.created_at)

    from_text = getattr(from_version, attribute_name)
    to_text = getattr(to_version, attribute_name)

    return text_diff_service.create_html_diff(
        from_text, to_text, from_description, to_description
    )
