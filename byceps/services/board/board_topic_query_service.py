"""
byceps.services.board.board_topic_query_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.sql import Select

from byceps.database import db, paginate, Pagination
from byceps.services.user import user_service
from byceps.services.user.dbmodels.user import DbUser
from byceps.services.user.models.user import User

from .dbmodels.category import DbBoardCategory
from .dbmodels.posting import DbPosting
from .dbmodels.topic import DbTopic
from .models import BoardCategoryID, BoardID, Topic, TopicID


def count_topics_for_board(board_id: BoardID) -> int:
    """Return the number of topics for that board."""
    return (
        db.session.scalar(
            select(db.func.count(DbTopic.id))
            .join(DbBoardCategory)
            .filter(DbBoardCategory.board_id == board_id)
        )
        or 0
    )


def find_topic(topic_id: TopicID) -> Topic | None:
    """Return the topic with that id, or `None` if not found."""
    db_topic = find_db_topic(topic_id)

    if db_topic is None:
        return None

    return _db_entity_to_topic(db_topic)


def find_db_topic(topic_id: TopicID) -> DbTopic | None:
    """Return the topic with that id, or `None` if not found."""
    return db.session.get(DbTopic, topic_id)


def get_db_topic(topic_id: TopicID) -> DbTopic:
    """Return the topic with that id."""
    db_topic = find_db_topic(topic_id)

    if db_topic is None:
        raise ValueError(f'Unknown topic ID "{topic_id}"')

    return db_topic


def find_topic_visible_for_user(
    topic_id: TopicID, *, include_hidden: bool = False
) -> DbTopic | None:
    """Return the topic with that id, or `None` if not found or
    invisible for the user.
    """
    stmt = (
        select(DbTopic)
        .options(
            db.joinedload(DbTopic.category),
        )
        .filter_by(id=topic_id)
    )

    if not include_hidden:
        stmt = stmt.filter_by(hidden=False)

    return db.session.scalars(stmt).unique().first()


def get_recent_topics(
    board_id: BoardID, limit: int, *, include_hidden: bool = False
) -> Sequence[DbTopic]:
    """Return recent topics in that board."""
    return (
        db.session.scalars(
            _select_topics(include_hidden=include_hidden)
            .join(DbBoardCategory)
            .filter(DbBoardCategory.board_id == board_id)
            .filter(DbBoardCategory.hidden == False)  # noqa: E712
            .order_by(DbTopic.last_updated_at.desc())
            .limit(limit)
        )
        .unique()
        .all()
    )


def paginate_topics(
    board_id: BoardID, page: int, per_page: int, *, include_hidden: bool = False
) -> Pagination:
    """Paginate topics in that board."""
    stmt = (
        _select_topics(include_hidden=include_hidden)
        .join(DbBoardCategory)
        .filter(DbBoardCategory.board_id == board_id)
        .filter(DbBoardCategory.hidden == False)  # noqa: E712
        .order_by(DbTopic.last_updated_at.desc())
    )

    return paginate(stmt, page, per_page)


def get_all_topic_ids_in_category(category_id: BoardCategoryID) -> set[TopicID]:
    """Return the IDs of all topics in the category."""
    topic_ids = db.session.scalars(
        select(DbTopic.id).filter(DbTopic.category_id == category_id)
    ).all()

    return set(topic_ids)


def paginate_topics_of_category(
    category_id: BoardCategoryID,
    page: int,
    per_page: int,
    *,
    include_hidden: bool = False,
) -> Pagination:
    """Paginate topics in that category, as visible for the user.

    Pinned topics are returned first.
    """
    stmt = (
        _select_topics(include_hidden=include_hidden)
        .filter_by(category_id=category_id)
        .order_by(DbTopic.pinned.desc(), DbTopic.last_updated_at.desc())
    )

    return paginate(stmt, page, per_page)


def _select_topics(*, include_hidden: bool = False) -> Select:
    stmt = select(DbTopic).options(
        db.joinedload(DbTopic.category),
        db.joinedload(DbTopic.last_updated_by),
        db.joinedload(DbTopic.hidden_by),
        db.joinedload(DbTopic.locked_by),
        db.joinedload(DbTopic.pinned_by),
    )

    if not include_hidden:
        stmt = stmt.filter_by(hidden=False)

    return stmt


def find_default_posting_to_jump_to(
    topic_id: TopicID, last_viewed_at: datetime, *, include_hidden: bool = False
) -> DbPosting | None:
    """Return the posting of the topic to show by default, or `None`."""
    postings_stmt = select(DbPosting).filter_by(topic_id=topic_id)

    if not include_hidden:
        postings_stmt = postings_stmt.filter_by(hidden=False)

    first_new_posting = db.session.scalars(
        postings_stmt.filter(DbPosting.created_at > last_viewed_at).order_by(
            DbPosting.created_at.asc()
        )
    ).first()

    if first_new_posting is None:
        # Current user has seen all postings so far, so show the last one.
        return db.session.scalars(
            postings_stmt.order_by(DbPosting.created_at.desc())
        ).first()

    return first_new_posting


def _db_entity_to_topic(db_topic: DbTopic) -> Topic:
    def to_user(db_user: DbUser | None) -> User | None:
        if db_user is None:
            return None

        return user_service._db_entity_to_user(db_user)

    creator = user_service.get_user(db_topic.creator_id)

    return Topic(
        id=db_topic.id,
        category_id=db_topic.category_id,
        created_at=db_topic.created_at,
        creator=creator,
        title=db_topic.title,
        posting_count=db_topic.posting_count,
        last_updated_at=db_topic.last_updated_at,
        last_updated_by=to_user(db_topic.last_updated_by),
        hidden=db_topic.hidden,
        hidden_at=db_topic.hidden_at,
        hidden_by=to_user(db_topic.hidden_by),
        locked=db_topic.locked,
        locked_at=db_topic.locked_at,
        locked_by=to_user(db_topic.locked_by),
        pinned=db_topic.pinned,
        pinned_at=db_topic.pinned_at,
        pinned_by=to_user(db_topic.pinned_by),
        initial_posting_id=db_topic.initial_posting.id,
        posting_limited_to_moderators=db_topic.posting_limited_to_moderators,
        muted=db_topic.muted,
    )
