"""
byceps.services.authn.api.authn_api_domain_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from datetime import datetime
from secrets import token_urlsafe

from byceps.services.authz.models import PermissionID
from byceps.services.user.models.user import UserID
from byceps.util.uuid import generate_uuid7

from .models import ApiToken


def create_api_token(
    creator_id: UserID,
    permissions: set[PermissionID],
    *,
    num_bytes: int = 40,
    description: str | None = None,
) -> ApiToken:
    """Create an API token."""
    api_token_id = generate_uuid7()
    created_at = datetime.utcnow()
    token = 'api_' + token_urlsafe(num_bytes)

    return ApiToken(
        id=api_token_id,
        created_at=created_at,
        creator_id=creator_id,
        token=token,
        permissions=frozenset(permissions),
        description=description,
        suspended=False,
    )
