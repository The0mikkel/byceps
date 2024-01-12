"""
byceps.scripts.validators
~~~~~~~~~~~~~~~~~~~~~~~~~

Validators for use with Click_.

.. _Click: https://click.palletsprojects.com/

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from uuid import UUID

import click

from byceps.services.brand import brand_service
from byceps.services.brand.models import Brand, BrandID
from byceps.services.party import party_service
from byceps.services.party.models import Party, PartyID
from byceps.services.site import site_service
from byceps.services.site.models import Site, SiteID
from byceps.services.user import user_service
from byceps.services.user.models.user import User, UserID


def validate_brand(ctx, param, brand_id: BrandID) -> Brand:
    brand = brand_service.find_brand(brand_id)

    if not brand:
        raise click.BadParameter(f'Unknown brand ID "{brand_id}".')

    return brand


def validate_party(ctx, param, party_id_value: str) -> Party:
    party = party_service.find_party(PartyID(party_id_value))

    if not party:
        raise click.BadParameter(f'Unknown party ID "{party_id_value}".')

    return party


def validate_site(ctx, param, site_id_value: str) -> Site:
    site = site_service.find_site(SiteID(site_id_value))

    if not site:
        raise click.BadParameter(f'Unknown site ID "{site_id_value}".')

    return site


def validate_user_id(ctx, param, user_id_value: str) -> User:
    user_id = validate_user_id_format(ctx, param, user_id_value)

    user = user_service.find_user(user_id)

    if not user:
        raise click.BadParameter(f'Unknown user ID "{user_id}".')

    return user


def validate_user_id_format(ctx, param, user_id_value: str) -> UserID:
    try:
        return UserID(UUID(user_id_value))
    except ValueError as exc:
        raise click.BadParameter(
            f'Invalid user ID "{user_id_value}": {exc}'
        ) from exc


def validate_user_screen_name(ctx, param, screen_name: str) -> User:
    user = user_service.find_user_by_screen_name(screen_name)

    if not user:
        raise click.BadParameter(f'Unknown user screen name "{screen_name}".')

    return user
