"""
byceps.services.user.dbmodels.detail
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship

from byceps.database import db
from byceps.services.user.models.user import UserID
from byceps.util.instances import ReprBuilder


class DbUserDetail(db.Model):
    """Detailed information about a specific user."""

    __tablename__ = 'user_details'

    user_id: Mapped[UserID] = mapped_column(
        db.Uuid, db.ForeignKey('users.id'), primary_key=True
    )
    user: Mapped['DbUser'] = relationship(  # noqa: F821, UP037
        'DbUser', backref=db.backref('detail', uselist=False)
    )
    first_name: Mapped[Optional[str]] = mapped_column(  # noqa: UP007
        db.UnicodeText
    )
    last_name: Mapped[Optional[str]] = mapped_column(  # noqa: UP007
        db.UnicodeText
    )
    date_of_birth: Mapped[Optional[date]]  # noqa: UP007
    country: Mapped[Optional[str]] = mapped_column(  # noqa: UP007
        db.UnicodeText
    )
    zip_code: Mapped[Optional[str]] = mapped_column(  # noqa: UP007
        db.UnicodeText
    )
    city: Mapped[Optional[str]] = mapped_column(db.UnicodeText)  # noqa: UP007
    street: Mapped[Optional[str]] = mapped_column(db.UnicodeText)  # noqa: UP007
    phone_number: Mapped[Optional[str]] = mapped_column(  # noqa: UP007
        db.UnicodeText
    )
    internal_comment: Mapped[Optional[str]] = mapped_column(  # noqa: UP007
        db.UnicodeText
    )
    extras: Mapped[Optional[Any]] = mapped_column(  # noqa: UP007
        MutableDict.as_mutable(db.JSONB)
    )

    @property
    def full_name(self) -> str | None:
        names = [self.first_name, self.last_name]
        return ' '.join(filter(None, names)) or None

    def __repr__(self) -> str:
        return (
            ReprBuilder(self)
            .add_with_lookup('user_id')
            .add_with_lookup('first_name')
            .add_with_lookup('last_name')
            .build()
        )
