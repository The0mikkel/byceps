"""
:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from byceps.services.board import (
    board_category_command_service,
    board_posting_command_service,
    board_posting_query_service,
    board_topic_command_service,
    board_topic_query_service,
)
from byceps.services.board.dbmodels.posting import DbPosting
from byceps.services.board.models import (
    BoardCategory,
    BoardCategoryID,
    BoardID,
    PostingID,
    Topic,
    TopicID,
)
from byceps.services.user.models.user import User

from tests.helpers import generate_token


def create_category(
    board_id: BoardID,
    *,
    number: int = 1,
    slug: str | None = None,
    title: str | None = None,
    description: str | None = None,
) -> BoardCategory:
    if slug is None:
        slug = generate_token()

    if title is None:
        title = generate_token()

    if description is None:
        description = f'Hier geht es um Kategorie {number}'

    return board_category_command_service.create_category(
        board_id, slug, title, description
    )


def create_topic(
    category_id: BoardCategoryID,
    creator: User,
    *,
    number: int = 1,
    title: str | None = None,
    body: str | None = None,
) -> Topic:
    if title is None:
        title = f'Thema {number}'

    if body is None:
        body = f'Inhalt von Thema {number}'

    topic, _ = board_topic_command_service.create_topic(
        category_id, creator, title, body
    )

    return topic


def create_posting(
    topic_id: TopicID,
    creator: User,
    *,
    number: int = 1,
    body: str | None = None,
) -> DbPosting:
    if body is None:
        body = f'Inhalt von Beitrag {number}.'

    posting, event = board_posting_command_service.create_posting(
        topic_id, creator, body
    )

    return posting


def find_topic(topic_id: TopicID) -> Topic | None:
    return board_topic_query_service.find_topic(topic_id)


def find_posting(posting_id: PostingID) -> DbPosting | None:
    return board_posting_query_service.find_db_posting(posting_id)
