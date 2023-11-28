"""
byceps.events.orga
~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import _BaseEvent, EventBrand, EventUser


@dataclass(frozen=True)
class _OrgaEvent(_BaseEvent):
    user: EventUser
    brand: EventBrand


@dataclass(frozen=True)
class OrgaStatusGrantedEvent(_OrgaEvent):
    pass


@dataclass(frozen=True)
class OrgaStatusRevokedEvent(_OrgaEvent):
    pass
