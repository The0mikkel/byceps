"""
byceps.services.ticketing.dbmodels.ticket
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship

from byceps.database import db
from byceps.services.party.models import PartyID
from byceps.services.seating.dbmodels.seat import DbSeat
from byceps.services.seating.models import SeatID
from byceps.services.shop.order.models.number import OrderNumber
from byceps.services.ticketing.models.ticket import (
    TicketBundleID,
    TicketCategoryID,
    TicketCode,
    TicketID,
)
from byceps.services.user.dbmodels.user import DbUser
from byceps.services.user.models.user import UserID
from byceps.util.instances import ReprBuilder
from byceps.util.uuid import generate_uuid7

from .category import DbTicketCategory
from .ticket_bundle import DbTicketBundle


class DbTicket(db.Model):
    """A ticket that permits to attend a party and to occupy a seat.

    A user can generally occupy multiple seats which is why no database
    constraints are in place to prevent that. However, if it makes sense
    for a party or party series, a user can be limited to occupy only a
    single seat by introducing custom guard code that blocks further
    attempts to reserve a seat.
    """

    __tablename__ = 'tickets'
    __table_args__ = (db.UniqueConstraint('party_id', 'code'),)

    id: Mapped[TicketID] = mapped_column(
        db.Uuid, default=generate_uuid7, primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    party_id: Mapped[PartyID] = mapped_column(
        db.UnicodeText, db.ForeignKey('parties.id'), index=True
    )
    code: Mapped[str] = mapped_column(db.UnicodeText, index=True)
    bundle_id: Mapped[TicketBundleID | None] = mapped_column(
        db.Uuid, db.ForeignKey('ticket_bundles.id'), index=True
    )
    bundle: Mapped[DbTicketBundle | None] = relationship(
        DbTicketBundle, backref='tickets'
    )
    category_id: Mapped[TicketCategoryID] = mapped_column(
        db.Uuid,
        db.ForeignKey('ticket_categories.id'),
        index=True,
    )
    category: Mapped[DbTicketCategory] = relationship(DbTicketCategory)
    owned_by_id: Mapped[UserID] = mapped_column(
        db.Uuid, db.ForeignKey('users.id'), index=True
    )
    owned_by: Mapped[DbUser] = relationship(DbUser, foreign_keys=[owned_by_id])
    order_number: Mapped[OrderNumber | None] = mapped_column(
        db.UnicodeText,
        db.ForeignKey('shop_orders.order_number'),
        index=True,
    )
    seat_managed_by_id: Mapped[UserID | None] = mapped_column(
        db.Uuid, db.ForeignKey('users.id'), index=True
    )
    seat_managed_by: Mapped[DbUser | None] = relationship(
        DbUser, foreign_keys=[seat_managed_by_id]
    )
    user_managed_by_id: Mapped[UserID | None] = mapped_column(
        db.Uuid, db.ForeignKey('users.id'), index=True
    )
    user_managed_by: Mapped[DbUser | None] = relationship(
        DbUser, foreign_keys=[user_managed_by_id]
    )
    occupied_seat_id: Mapped[SeatID | None] = mapped_column(
        db.Uuid,
        db.ForeignKey('seats.id'),
        index=True,
        unique=True,
    )
    occupied_seat: Mapped[DbSeat | None] = relationship(
        DbSeat, backref=db.backref('occupied_by_ticket', uselist=False)
    )
    used_by_id: Mapped[UserID | None] = mapped_column(
        db.Uuid, db.ForeignKey('users.id'), index=True
    )
    used_by: Mapped[DbUser | None] = relationship(
        DbUser, foreign_keys=[used_by_id]
    )
    revoked: Mapped[bool] = mapped_column(default=False)
    user_checked_in: Mapped[bool] = mapped_column(default=False)

    def __init__(
        self,
        party_id: PartyID,
        code: TicketCode,
        category_id: TicketCategoryID,
        owned_by_id: UserID,
        *,
        bundle: DbTicketBundle | None = None,
        order_number: OrderNumber | None = None,
        used_by_id: UserID | None = None,
    ) -> None:
        self.party_id = party_id
        self.code = code
        self.bundle = bundle
        self.category_id = category_id
        self.owned_by_id = owned_by_id
        self.order_number = order_number
        self.used_by_id = used_by_id

    @property
    def belongs_to_bundle(self) -> bool:
        """Return `True` if this ticket is part of a ticket bundle, or
        `False` if it is stand-alone.
        """
        return self.bundle_id is not None

    def is_owned_by(self, user_id: UserID):
        """Return `True` if the user owns this ticket."""
        return self.owned_by_id == user_id

    def get_seat_manager(self) -> DbUser:
        """Return the user that may choose the seat for this ticket."""
        return self.seat_managed_by or self.owned_by

    def get_user_manager(self) -> DbUser:
        """Return the user that may choose the user of this ticket."""
        return self.user_managed_by or self.owned_by

    def is_managed_by(self, user_id: UserID) -> bool:
        """Return `True` if the user may choose the seat for or the
        user of this ticket.
        """
        return self.is_seat_managed_by(user_id) or self.is_user_managed_by(
            user_id
        )

    def is_seat_managed_by(self, user_id: UserID) -> bool:
        """Return `True` if the user may choose the seat for this ticket."""
        return (
            (self.seat_managed_by_id is None) and self.is_owned_by(user_id)
        ) or (self.seat_managed_by_id == user_id)

    def is_user_managed_by(self, user_id: UserID) -> bool:
        """Return `True` if the user may choose the user of this ticket."""
        return (
            (self.user_managed_by_id is None) and self.is_owned_by(user_id)
        ) or (self.user_managed_by_id == user_id)

    def __repr__(self) -> str:
        def user(user: DbUser | None) -> str | None:
            return user.screen_name if (user is not None) else None

        def occupied_seat() -> str | None:
            seat = self.occupied_seat

            if seat is None:
                return None

            return f'{{area={seat.area.title!r}, label={seat.label!r}}}'

        return (
            ReprBuilder(self)
            .add('id', str(self.id))
            .add('party_id', self.party_id)
            .add('code', self.code)
            .add('category', self.category.title)
            .add('owned_by', user(self.owned_by))
            .add_custom(f'occupied_seat={occupied_seat()}')
            .add('used_by', user(self.used_by))
            .build()
        )
