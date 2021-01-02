"""
byceps.services.tourney.models.tourney
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2021 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from datetime import datetime
from typing import Optional

from ....database import db, generate_uuid

from ....util.instances import ReprBuilder

from ..transfer.models import TourneyCategoryID

from .tourney_category import TourneyCategory


class Tourney(db.Model):
    """A tournament."""

    __tablename__ = 'tourneys'
    __table_args__ = (
        db.UniqueConstraint('category_id', 'title'),
    )

    id = db.Column(db.Uuid, default=generate_uuid, primary_key=True)
    title = db.Column(db.UnicodeText, nullable=False)
    subtitle = db.Column(db.UnicodeText, nullable=True)
    logo_url = db.Column(db.UnicodeText, nullable=True)
    category_id = db.Column(
        db.Uuid,
        db.ForeignKey('tourney_categories.id'),
        index=True,
        nullable=False,
    )
    category = db.relationship(TourneyCategory)
    max_participant_count = db.Column(db.Integer, nullable=False)
    starts_at = db.Column(db.DateTime, nullable=False)

    def __init__(
        self,
        title: str,
        category_id: TourneyCategoryID,
        max_participant_count: int,
        starts_at: datetime,
        *,
        subtitle: Optional[str] = None,
        logo_url: Optional[str] = None,
    ) -> None:
        self.title = title
        self.subtitle = subtitle
        self.logo_url = logo_url
        self.category_id = category_id
        self.max_participant_count = max_participant_count
        self.starts_at = starts_at

    def __repr__(self) -> str:
        return ReprBuilder(self) \
            .add_with_lookup('title') \
            .build()
