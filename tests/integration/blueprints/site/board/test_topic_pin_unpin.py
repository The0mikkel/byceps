"""
:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from byceps.database import db
from byceps.services.board import board_topic_command_service

from .helpers import find_topic


BASE_URL = 'http://www.acmecon.test'


def test_pin_topic(site_app, moderator, moderator_client, topic):
    topic_before = topic

    assert_topic_is_not_pinned(topic_before)

    url = f'{BASE_URL}/board/topics/{topic_before.id}/flags/pinned'
    response = moderator_client.post(url)

    assert response.status_code == 204

    db.session.expire_all()

    topic_afterwards = find_topic(topic_before.id)
    assert_topic_is_pinned(topic_afterwards, moderator.id)


def test_unpin_topic(site_app, moderator, moderator_client, topic):
    topic_before = topic

    board_topic_command_service.pin_topic(topic_before.id, moderator)
    topic_before = find_topic(topic_before.id)

    assert_topic_is_pinned(topic_before, moderator.id)

    url = f'{BASE_URL}/board/topics/{topic_before.id}/flags/pinned'
    response = moderator_client.delete(url)

    assert response.status_code == 204

    db.session.expire_all()

    topic_afterwards = find_topic(topic_before.id)
    assert_topic_is_not_pinned(topic_afterwards)


def assert_topic_is_pinned(topic, moderator_id):
    assert topic.pinned
    assert topic.pinned_at is not None
    assert topic.pinned_by.id == moderator_id


def assert_topic_is_not_pinned(topic):
    assert not topic.pinned
    assert topic.pinned_at is None
    assert topic.pinned_by is None
