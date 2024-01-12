"""
byceps.services.orga.orga_birthday_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from collections.abc import Iterable, Iterator
from itertools import islice

from sqlalchemy import select

from byceps.database import db
from byceps.services.user import user_avatar_service
from byceps.services.user.dbmodels.detail import DbUserDetail
from byceps.services.user.dbmodels.user import DbUser
from byceps.services.user.models.user import User, UserID

from .dbmodels import DbOrgaFlag
from .models import Birthday


def get_orgas_with_birthday_today() -> set[User]:
    """Return the orgas whose birthday is today."""
    orgas_with_birthdays = _collect_orgas_with_known_birthdays()

    return {
        user for user, birthday in orgas_with_birthdays if birthday.is_today
    }


def collect_orgas_with_next_birthdays(
    *, limit: int | None = None
) -> list[tuple[User, Birthday]]:
    """Return the next birthdays of organizers, sorted by month and day."""
    orgas_with_birthdays = _collect_orgas_with_known_birthdays()

    sorted_orgas = sort_users_by_next_birthday(orgas_with_birthdays)

    if limit is not None:
        sorted_orgas = list(islice(sorted_orgas, limit))

    return sorted_orgas


def _collect_orgas_with_known_birthdays() -> Iterator[tuple[User, Birthday]]:
    """Yield all organizers whose birthday is known."""
    users = (
        db.session.scalars(
            select(DbUser)
            .join(DbOrgaFlag)
            .join(DbUserDetail)
            .filter(DbUserDetail.date_of_birth.is_not(None))
            .options(db.joinedload(DbUser.detail))
        )
        .unique()
        .all()
    )

    user_ids = {user.id for user in users}
    avatar_urls_by_user_id = user_avatar_service.get_avatar_urls_for_users(
        user_ids
    )

    for user in users:
        user_dto = _to_user_dto(user, avatar_urls_by_user_id)
        birthday = Birthday(user.detail.date_of_birth)
        yield user_dto, birthday


def _to_user_dto(
    user: DbUser, avatar_urls_by_user_id: dict[UserID, str | None]
) -> User:
    """Create user DTO from database entity."""
    avatar_url = avatar_urls_by_user_id.get(user.id)

    return User(
        id=user.id,
        screen_name=user.screen_name,
        initialized=user.initialized,
        suspended=user.suspended,
        deleted=user.deleted,
        locale=user.locale,
        avatar_url=avatar_url,
    )


def sort_users_by_next_birthday(
    users_and_birthdays: Iterable[tuple[User, Birthday]],
) -> list[tuple[User, Birthday]]:
    return list(
        sorted(
            users_and_birthdays,
            key=lambda user_and_birthday: (
                user_and_birthday[1].days_until_next_birthday,
                -(user_and_birthday[1].age or 0),
            ),
        )
    )
