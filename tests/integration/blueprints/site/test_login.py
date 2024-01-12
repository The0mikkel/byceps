"""
:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

import pytest

from byceps.services.authn.session import authn_session_service
from byceps.services.consent import (
    brand_requirements_service,
    consent_subject_service,
)
from byceps.services.user import user_log_service

from tests.helpers import generate_token


BASE_URL = 'http://www.acmecon.test'


@pytest.fixture()
def client(site_app, site):
    return site_app.test_client()


def test_login_form(client):
    url = f'{BASE_URL}/authentication/log_in'

    response = client.get(url)

    assert response.status_code == 200


def test_login_succeeds(site, client, make_user):
    password = 'correct horse battery staple'

    user = make_user(password=password)

    login_log_entries_before = user_log_service.get_entries_of_type_for_user(
        user.id, 'user-logged-in'
    )
    assert len(login_log_entries_before) == 0

    assert authn_session_service.find_recent_login(user.id) is None

    assert get_session_cookie(client) is None

    url = f'{BASE_URL}/authentication/log_in'
    form_data = {
        'username': user.screen_name,
        'password': password,
    }

    response = client.post(url, data=form_data)
    assert response.status_code == 204
    # Location (used by JavaScript redirect) should point to user
    # user dashboard.
    assert response.location == '/dashboard'

    login_log_entries_after = user_log_service.get_entries_of_type_for_user(
        user.id, 'user-logged-in'
    )
    assert len(login_log_entries_after) == 1
    login_log_entry = login_log_entries_after[0]
    assert login_log_entry.data == {
        'ip_address': '127.0.0.1',
        'site_id': site.id,
    }

    assert authn_session_service.find_recent_login(user.id) is not None

    cookie = get_session_cookie(client)
    assert cookie is not None
    assert cookie.secure


def test_login_fails_with_invalid_credentials(client):
    url = f'{BASE_URL}/authentication/log_in'
    form_data = {
        'username': 'TotallyUnknownUser',
        'password': 'TotallyWrongPassword',
    }

    response = client.post(url, data=form_data)
    assert response.status_code == 401

    assert get_session_cookie(client) is None


def test_login_fails_lacking_consent(client, brand, make_user):
    subject_name = generate_token()
    subject = consent_subject_service.create_subject(
        subject_name, subject_name, 'agree', None
    )
    brand_requirements_service.create_brand_requirement(brand.id, subject.id)

    password = 'the password is not the problem'

    user = make_user(password=password)

    form_data = {
        'username': user.screen_name,
        'password': password,
    }

    response = client.post(f'{BASE_URL}/authentication/log_in', data=form_data)
    assert response.status_code == 204
    assert response.location.startswith('/consent/consent/')

    brand_requirements_service.delete_brand_requirement(brand.id, subject.id)

    assert get_session_cookie(client) is None


def get_session_cookie(client):
    return client.get_cookie('session', domain='www.acmecon.test')
