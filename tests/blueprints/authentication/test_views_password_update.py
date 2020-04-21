"""
:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

import pytest

from byceps.services.authentication.password.models import Credential
from byceps.services.authentication.password import service as password_service
from byceps.services.authentication.session import service as session_service
from byceps.services.site import service as site_service

from tests.helpers import create_site, create_user, http_client, login_user


@pytest.fixture(scope='module')
def site(party_app_with_db, make_email_config):
    make_email_config()
    site = create_site()
    yield site
    site_service.delete_site(site.id)


def test_when_logged_in_endpoint_is_available(party_app_with_db, site):
    old_password = 'LekkerBratworsten'
    new_password = 'EvenMoreSecure!!1'

    user = create_user()
    password_service.create_password_hash(user.id, old_password)
    login_user(user.id)

    credential_before = find_credential(user.id)
    assert credential_before is not None

    password_hash_before = credential_before.password_hash
    credential_updated_at_before = credential_before.updated_at
    assert password_hash_before is not None
    assert credential_updated_at_before is not None

    session_token_before = find_session_token(user.id)
    assert session_token_before is not None

    form_data = {
        'old_password': old_password,
        'new_password': new_password,
        'new_password_confirmation': new_password,
    }

    response = send_request(party_app_with_db, form_data, user_id=user.id)

    assert response.status_code == 302
    assert response.headers.get('Location') == 'http://example.com/authentication/login'

    credential_after = find_credential(user.id)
    session_token_after = find_session_token(user.id)

    assert credential_after is not None
    assert password_hash_before != credential_after.password_hash
    assert credential_updated_at_before != credential_after.updated_at

    # Session token should have been removed after password change.
    assert session_token_after is None


def test_when_not_logged_in_endpoint_is_unavailable(party_app_with_db, site):
    form_data = {}

    response = send_request(party_app_with_db, form_data)

    assert response.status_code == 404


# helpers


def find_credential(user_id):
    return Credential.query.get(user_id)


def find_session_token(user_id):
    return session_service.find_session_token_for_user(user_id)


def send_request(app, form_data, *, user_id=None):
    url = '/authentication/password'
    with http_client(app, user_id=user_id) as client:
        return client.post(url, data=form_data)
