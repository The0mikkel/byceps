"""
:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from byceps.database import db
from byceps.services.board import board_posting_command_service

from .helpers import find_posting


BASE_URL = 'http://www.acmecon.test'


def test_hide_posting(site_app, moderator, moderator_client, posting):
    posting_before = posting

    assert_posting_is_not_hidden(posting_before)

    url = f'{BASE_URL}/board/postings/{posting_before.id}/flags/hidden'
    response = moderator_client.post(url)

    assert response.status_code == 204

    db.session.expire_all()

    posting_afterwards = find_posting(posting_before.id)
    assert_posting_is_hidden(posting_afterwards, moderator.id)


def test_unhide_posting(site_app, moderator, moderator_client, posting):
    posting_before = posting

    board_posting_command_service.hide_posting(posting_before.id, moderator)

    assert_posting_is_hidden(posting_before, moderator.id)

    url = f'{BASE_URL}/board/postings/{posting_before.id}/flags/hidden'
    response = moderator_client.delete(url)

    assert response.status_code == 204

    db.session.expire_all()

    posting_afterwards = find_posting(posting_before.id)
    assert_posting_is_not_hidden(posting_afterwards)


def assert_posting_is_hidden(posting, moderator_id):
    assert posting.hidden
    assert posting.hidden_at is not None
    assert posting.hidden_by_id == moderator_id


def assert_posting_is_not_hidden(posting):
    assert not posting.hidden
    assert posting.hidden_at is None
    assert posting.hidden_by_id is None
