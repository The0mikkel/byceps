"""
:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from byceps.services.authn.session import authn_session_service
from byceps.services.authn.session.models import CurrentUser
from byceps.services.user.models.user import User


def get_current_user_for_user(user: User, locale: str) -> CurrentUser:
    return authn_session_service.get_authenticated_current_user(
        user, locale=locale, permissions=frozenset()
    )
