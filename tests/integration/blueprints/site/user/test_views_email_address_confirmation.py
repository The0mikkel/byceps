"""
:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

import pytest

from byceps.database import db
from byceps.services.authz import authz_service
from byceps.services.user import user_service
from byceps.services.verification_token import verification_token_service

from tests.helpers import http_client


@pytest.fixture(scope='module')
def user1(make_user):
    return make_user(email_address='user1@mail.test', initialized=False)


@pytest.fixture(scope='module')
def user2(make_user):
    return make_user(initialized=False)


@pytest.fixture(scope='module')
def user3(make_user):
    return make_user(email_address='user3@mail.test', initialized=True)


@pytest.fixture(scope='module')
def user4(make_user):
    return make_user(initialized=True)


@pytest.fixture(scope='module')
def user5(make_user):
    return make_user(email_address='user5@mail.test', initialized=True)


@pytest.fixture(scope='module')
def test_valid_token(site_app, user1):
    user = user1
    user_id = user.id

    user_before = user_service.get_db_user(user_id)
    assert not user_before.email_address_verified
    assert not user_before.initialized
    assert 'board_user' not in get_role_ids(user_id)

    token = create_verification_token(user, 'user1@mail.test')

    # -------------------------------- #

    response = confirm(site_app, token)

    # -------------------------------- #

    assert response.status_code == 302

    user_after = user_service.get_db_user(user_id)
    assert user_after.email_address_verified
    assert user_after.initialized
    assert 'board_user' in get_role_ids(user_id)


def test_unknown_token(site_app, site, user2):
    user_id = user2.id

    user_before = user_service.get_db_user(user_id)
    assert not user_before.initialized

    unknown_token = 'wZdSLzkT-zRf2x2T6AR7yGa3Nc_X3Nn3F3XGPvPtOhw'

    # -------------------------------- #

    response = confirm(site_app, unknown_token)

    # -------------------------------- #

    assert response.status_code == 200

    user_after = user_service.get_db_user(user_id)
    assert not user_after.initialized

    assert get_role_ids(user_id) == set()


def test_initialized_user(site_app, user3):
    user = user3
    user_id = user.id

    user_before = user_service.get_db_user(user_id)
    assert not user_before.email_address_verified
    assert user_before.initialized

    token = create_verification_token(user, 'user3@mail.test')

    # -------------------------------- #

    response = confirm(site_app, token)

    # -------------------------------- #

    assert response.status_code == 302

    user_after = user_service.get_db_user(user_id)
    assert user_after.email_address_verified
    assert user_after.initialized


def test_account_without_email_address(site_app, site, user4):
    user = user4
    user_id = user.id

    user_with_email_address = user_service.get_db_user(user_id)
    user_with_email_address.email_address = None
    db.session.commit()

    user_before = user_service.get_db_user(user_id)
    assert user_before.email_address is None
    assert not user_before.email_address_verified
    assert user_before.initialized

    token = create_verification_token(user, 'user4@mail.test')

    # -------------------------------- #

    response = confirm(site_app, token)

    # -------------------------------- #

    assert response.status_code == 302

    user_after = user_service.get_db_user(user_id)
    assert not user_after.email_address_verified


def test_different_user_and_token_email_addresses(site_app, site, user5):
    user = user5
    user_id = user.id

    user_before = user_service.get_db_user(user_id)
    assert not user_before.email_address_verified
    assert user_before.initialized

    token = create_verification_token(user, 'user5@mail-other.test')

    # -------------------------------- #

    response = confirm(site_app, token)

    # -------------------------------- #

    assert response.status_code == 302

    user_after = user_service.get_db_user(user_id)
    assert not user_after.email_address_verified


# helpers


def confirm(app, token):
    url = f'http://www.acmecon.test/users/email_address/confirmation/{token}'
    with http_client(app) as client:
        return client.post(url)


def get_role_ids(user_id):
    return authz_service.find_role_ids_for_user(user_id)


def create_verification_token(user, email_address):
    confirmation_token = (
        verification_token_service.create_for_email_address_confirmation(
            user, email_address
        )
    )
    return confirmation_token.token
