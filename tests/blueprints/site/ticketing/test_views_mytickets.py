"""
:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

import pytest

from byceps.services.brand import service as brand_service
from byceps.services.party import service as party_service
from byceps.services.site import service as site_service

from tests.helpers import (
    create_brand,
    create_party,
    create_site,
    http_client,
    login_user,
)


@pytest.fixture(scope='module')
def brand(party_app_with_db):
    brand = create_brand()
    yield brand
    brand_service.delete_brand(brand.id)


@pytest.fixture(scope='module')
def party(brand):
    party = create_party(brand.id)
    yield party
    party_service.delete_party(party.id)


@pytest.fixture(scope='module')
def site(party_app_with_db, make_email_config, party):
    make_email_config()
    site = create_site(party_id=party.id)
    yield site
    site_service.delete_site(site.id)


def test_when_logged_in(party_app_with_db, site, user):
    login_user(user.id)

    response = send_request(party_app_with_db, user_id=user.id)

    assert response.status_code == 200
    assert response.mimetype == 'text/html'


def test_when_not_logged_in(party_app_with_db, site):
    response = send_request(party_app_with_db)

    assert response.status_code == 302
    assert 'Location' in response.headers


# helpers


def send_request(app, user_id=None):
    url = '/tickets/mine'
    with http_client(app, user_id=user_id) as client:
        return client.get(url)
