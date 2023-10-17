"""
byceps.services.user_badge.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import NewType
from uuid import UUID

from byceps.services.brand.models import BrandID
from byceps.services.user.models.user import UserID


BadgeID = NewType('BadgeID', UUID)


@dataclass(frozen=True)
class Badge:
    id: BadgeID
    slug: str
    label: str
    description: str | None
    image_filename: str
    image_url_path: str
    brand_id: BrandID | None
    featured: bool


@dataclass(frozen=True)
class BadgeAwarding:
    id: UUID
    badge_id: BadgeID
    awardee_id: UserID
    awarded_at: datetime


@dataclass(frozen=True)
class QuantifiedBadgeAwarding:
    badge_id: BadgeID
    awardee_id: UserID
    quantity: int
