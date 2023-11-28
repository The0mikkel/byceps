"""
byceps.events.authz
~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from __future__ import annotations

from dataclasses import dataclass

from byceps.services.authz.models import RoleID

from .base import _BaseEvent, EventUser


@dataclass(frozen=True)
class _AuthzUserRoleEvent(_BaseEvent):
    user: EventUser
    role_id: RoleID


@dataclass(frozen=True)
class RoleAssignedToUserEvent(_AuthzUserRoleEvent):
    pass


@dataclass(frozen=True)
class RoleDeassignedFromUserEvent(_AuthzUserRoleEvent):
    pass
