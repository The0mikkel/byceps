"""
byceps.events.user_badge
~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from dataclasses import dataclass

from byceps.services.user_badge.models import BadgeID

from .base import _BaseEvent, EventUser


@dataclass(frozen=True)
class UserBadgeAwardedEvent(_BaseEvent):
    badge_id: BadgeID
    badge_label: str
    awardee: EventUser
