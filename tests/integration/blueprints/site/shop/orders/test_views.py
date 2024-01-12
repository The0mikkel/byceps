"""
:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from moneyed import EUR
import pytest

from byceps.services.shop.cart.models import Cart
from byceps.services.shop.order import order_checkout_service
from byceps.services.shop.storefront.models import Storefront
from byceps.services.site import site_service
from byceps.services.snippet import snippet_service

from tests.helpers import create_site, http_client, log_in_user
from tests.helpers.shop import create_shop_snippet


@pytest.fixture()
def shop1(admin_app, make_brand, make_shop, admin_user):
    brand = make_brand()
    shop = make_shop(brand.id)
    snippet_id = create_payment_instructions_snippet(shop.id, admin_user)

    yield shop

    snippet_service.delete_snippet(snippet_id)


@pytest.fixture()
def shop2(admin_app, make_brand, make_shop):
    brand = make_brand()
    shop = make_shop(brand.id)

    return shop


@pytest.fixture()
def storefront1(
    shop1, make_order_number_sequence, make_storefront
) -> Storefront:
    order_number_sequence = make_order_number_sequence(shop1.id)

    return make_storefront(shop1.id, order_number_sequence.id)


@pytest.fixture()
def storefront2(
    shop2, make_order_number_sequence, make_storefront
) -> Storefront:
    order_number_sequence = make_order_number_sequence(shop2.id)

    return make_storefront(shop2.id, order_number_sequence.id)


@pytest.fixture()
def site1(brand, storefront1):
    site = create_site('site1', brand.id, storefront_id=storefront1.id)
    yield site
    site_service.delete_site(site.id)


@pytest.fixture()
def site2(brand, storefront2):
    site = create_site('site2', brand.id, storefront_id=storefront2.id)
    yield site
    site_service.delete_site(site.id)


@pytest.fixture()
def site1_app(site1, make_site_app):
    server_name = 'site-for-orders-1.acmecon.test'
    app = make_site_app(server_name, site1.id)
    with app.app_context():
        yield app


@pytest.fixture()
def site2_app(site2, make_site_app):
    server_name = 'site-for-orders-2.acmecon.test'
    app = make_site_app(server_name, site2.id)
    with app.app_context():
        yield app


@pytest.fixture(scope='module')
def user1(make_user):
    return make_user()


@pytest.fixture(scope='module')
def user2(make_user):
    return make_user()


@pytest.fixture()
def order(make_orderer, storefront1, user1):
    orderer = make_orderer(user1)
    cart = Cart(EUR)

    order, _ = order_checkout_service.place_order(
        storefront1, orderer, cart
    ).unwrap()

    return order


def test_view_matching_user_and_site_and_shop(site1_app, order, user1):
    response = request_view(site1_app, user1, order.id)

    assert response.status_code == 200


def test_view_matching_site_and_shop_but_different_user(
    site1_app, order, user1, user2
):
    response = request_view(site1_app, user2, order.id)

    assert response.status_code == 404


def test_view_matching_user_but_different_site_and_shop(
    site2_app, order, user1
):
    response = request_view(site2_app, user1, order.id)

    assert response.status_code == 404


# helpers


def create_payment_instructions_snippet(shop_id, admin):
    body = 'Please pay {{ total_amount }} for order {{ order_number }}!'
    return create_shop_snippet(
        shop_id, admin, 'payment_instructions', 'de', body
    )


def request_view(app, current_user, order_id):
    log_in_user(current_user.id)

    server_name = app.config['SERVER_NAME']
    url = f'http://{server_name}/shop/orders/{order_id}'

    with http_client(app, user_id=current_user.id) as client:
        response = client.get(url)

    return response
