"""
:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

import pytest

from byceps.services.tourney import (
    tourney_match_comment_service,
    tourney_match_service,
)


def test_update_comment(api_client, api_client_authz_header, comment, user):
    original_comment = tourney_match_comment_service.get_comment(comment.id)
    assert original_comment.body_text == 'Something stupid.'
    assert original_comment.body_html == 'Something stupid.'
    assert original_comment.last_edited_at is None
    assert original_comment.last_edited_by is None

    response = request_comment_update(
        api_client, api_client_authz_header, comment.id, user.id
    )

    assert response.status_code == 204

    updated_comment = tourney_match_comment_service.get_comment(comment.id)
    assert updated_comment.body_text == '[i]This[/i] is better!'
    assert updated_comment.body_html == '<em>This</em> is better!'
    assert updated_comment.last_edited_at is not None
    assert updated_comment.last_edited_by is not None
    assert updated_comment.last_edited_by.id == user.id


def test_update_nonexistent_comment(api_client, api_client_authz_header, user):
    unknown_comment_id = '00000000-0000-0000-0000-000000000000'

    response = request_comment_update(
        api_client, api_client_authz_header, unknown_comment_id, user.id
    )

    assert response.status_code == 404


# helpers


@pytest.fixture()
def match(database):
    return tourney_match_service.create_match()


@pytest.fixture()
def comment(match, user):
    body = 'Something stupid.'

    return tourney_match_comment_service.create_comment(match.id, user, body)


def request_comment_update(
    api_client, api_client_authz_header, comment_id, editor_id
):
    url = f'http://api.acmecon.test/v1/tourney/match_comments/{comment_id}'

    headers = [api_client_authz_header]
    json_data = {
        'editor_id': editor_id,
        'body': '[i]This[/i] is better!',
    }

    return api_client.patch(url, headers=headers, json=json_data)
