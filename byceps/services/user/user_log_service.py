"""
byceps.services.user.user_log_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from datetime import datetime

from sqlalchemy import select

from byceps.database import db
from byceps.services.user.models.user import UserID
from byceps.util.uuid import generate_uuid7

from .dbmodels.log import DbUserLogEntry
from .models.log import UserLogEntry, UserLogEntryData


def create_entry(
    event_type: str,
    user_id: UserID,
    data: UserLogEntryData,
    *,
    occurred_at: datetime | None = None,
) -> None:
    """Create a user log entry."""
    db_entry = build_entry(event_type, user_id, data, occurred_at=occurred_at)

    db.session.add(db_entry)
    db.session.commit()


def build_entry(
    event_type: str,
    user_id: UserID,
    data: UserLogEntryData,
    *,
    occurred_at: datetime | None = None,
    initiator_id: UserID | None = None,
) -> DbUserLogEntry:
    """Assemble, but not persist, a user log entry."""
    entry_id = generate_uuid7()

    if occurred_at is None:
        occurred_at = datetime.utcnow()

    return DbUserLogEntry(
        entry_id, occurred_at, event_type, user_id, initiator_id, data
    )


def to_db_entry(entry: UserLogEntry) -> DbUserLogEntry:
    """Convert log entry to database entity."""
    return DbUserLogEntry(
        entry.id,
        entry.occurred_at,
        entry.event_type,
        entry.user_id,
        entry.initiator_id,
        entry.data,
    )


def get_entries_for_user(user_id: UserID) -> list[UserLogEntry]:
    """Return the log entries for that user."""
    db_entries = db.session.scalars(
        select(DbUserLogEntry)
        .filter_by(user_id=user_id)
        .order_by(DbUserLogEntry.occurred_at)
    ).all()

    return [_db_entity_to_entry(db_entry) for db_entry in db_entries]


def get_entries_of_type_for_user(
    user_id: UserID, event_type: str
) -> list[UserLogEntry]:
    """Return the log entries of that type for that user."""
    db_entries = db.session.scalars(
        select(DbUserLogEntry)
        .filter_by(user_id=user_id)
        .filter_by(event_type=event_type)
        .order_by(DbUserLogEntry.occurred_at)
    ).all()

    return [_db_entity_to_entry(db_entry) for db_entry in db_entries]


def _db_entity_to_entry(db_entry: DbUserLogEntry) -> UserLogEntry:
    return UserLogEntry(
        id=db_entry.id,
        occurred_at=db_entry.occurred_at,
        event_type=db_entry.event_type,
        user_id=db_entry.user_id,
        initiator_id=db_entry.initiator_id,
        data=db_entry.data.copy(),
    )
