"""
:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from collections.abc import Iterable
from unittest.mock import patch

from flask import Flask
from moneyed import EUR
import pytest

from byceps.database import db
from byceps.events.base import EventUser
from byceps.events.shop import ShopOrderCanceledEvent, ShopOrderPaidEvent
from byceps.services.shop.article import article_service
from byceps.services.shop.article.models import (
    Article,
    ArticleID,
    ArticleNumber,
)
from byceps.services.shop.cart.models import Cart
from byceps.services.shop.order import order_checkout_service, order_service
from byceps.services.shop.order.dbmodels.order import DbOrder
from byceps.services.shop.order.models.order import (
    Order,
    Orderer,
    OrderID,
    PaymentState,
)
from byceps.services.shop.shop.models import Shop
from byceps.services.shop.storefront.models import Storefront
from byceps.services.user.models.user import User, UserID

from tests.helpers import log_in_user


BASE_URL = 'http://admin.acmecon.test'


@pytest.fixture(scope='package')
def shop_order_admin(make_admin) -> User:
    permission_ids = {
        'admin.access',
        'shop_order.cancel',
        'shop_order.mark_as_paid',
    }
    admin = make_admin(permission_ids)
    log_in_user(admin.id)
    return admin


@pytest.fixture(scope='package')
def shop_order_admin_client(
    make_client, admin_app: Flask, shop_order_admin: User
):
    return make_client(admin_app, user_id=shop_order_admin.id)


@pytest.fixture()
def article1(make_article, shop: Shop) -> Article:
    return make_article(
        shop.id,
        item_number=ArticleNumber('item-001'),
        description='Item #1',
        total_quantity=8,
    )


@pytest.fixture()
def article2(make_article, shop: Shop) -> Article:
    return make_article(
        shop.id,
        item_number=ArticleNumber('item-002'),
        description='Item #2',
        total_quantity=8,
    )


@pytest.fixture()
def article3(make_article, shop: Shop) -> Article:
    return make_article(
        shop.id,
        item_number=ArticleNumber('item-003'),
        description='Item #3',
        total_quantity=8,
    )


@pytest.fixture(scope='module')
def orderer_user(make_user) -> User:
    return make_user()


@pytest.fixture(scope='module')
def orderer(make_orderer, orderer_user: User) -> Orderer:
    return make_orderer(orderer_user)


@patch('byceps.signals.shop.order_canceled.send')
@patch('byceps.blueprints.admin.shop.order.views.order_email_service')
def test_cancel_before_paid(
    order_email_service_mock,
    order_canceled_signal_send_mock,
    storefront: Storefront,
    article1: Article,
    shop_order_admin: User,
    orderer_user: User,
    orderer: Orderer,
    shop_order_admin_client,
):
    article = article1

    quantified_articles_to_order = [(article, 3)]
    placed_order = place_order(
        storefront, orderer, quantified_articles_to_order
    )
    db_order_before = get_db_order(placed_order.id)

    assert get_article_quantity(article.id) == 5

    assert_payment_is_open(db_order_before)

    url = f'{BASE_URL}/shop/orders/{db_order_before.id}/cancel'
    form_data = {
        'reason': 'Dein Vorname ist albern!',
        'send_email': 'y',
    }
    response = shop_order_admin_client.post(url, data=form_data)

    db_order_afterwards = get_db_order(db_order_before.id)
    assert response.status_code == 302
    assert_payment(
        db_order_afterwards,
        None,
        PaymentState.canceled_before_paid,
        shop_order_admin.id,
    )

    assert get_article_quantity(article.id) == 8

    order_afterwards = order_service.get_order(placed_order.id)

    order_email_service_mock.send_email_for_canceled_order_to_orderer.assert_called_once_with(
        order_afterwards
    )

    event = ShopOrderCanceledEvent(
        occurred_at=db_order_afterwards.payment_state_updated_at,
        initiator=EventUser.from_user(shop_order_admin),
        order_id=placed_order.id,
        order_number=placed_order.order_number,
        orderer=EventUser.from_user(orderer_user),
    )
    order_canceled_signal_send_mock.assert_called_once_with(None, event=event)


@patch('byceps.signals.shop.order_canceled.send')
@patch('byceps.blueprints.admin.shop.order.views.order_email_service')
def test_cancel_before_paid_without_sending_email(
    order_email_service_mock,
    order_canceled_signal_send_mock,
    storefront: Storefront,
    article2: Article,
    shop_order_admin: User,
    orderer_user: User,
    orderer: Orderer,
    shop_order_admin_client,
):
    article = article2

    quantified_articles_to_order = [(article, 3)]
    placed_order = place_order(
        storefront, orderer, quantified_articles_to_order
    )

    url = f'{BASE_URL}/shop/orders/{placed_order.id}/cancel'
    form_data = {
        'reason': 'Dein Vorname ist albern!',
        # Sending e-mail is not requested.
    }
    response = shop_order_admin_client.post(url, data=form_data)

    db_order_afterwards = get_db_order(placed_order.id)
    assert response.status_code == 302

    # No e-mail should be send.
    order_email_service_mock.send_email_for_canceled_order_to_orderer.assert_not_called()

    event = ShopOrderCanceledEvent(
        occurred_at=db_order_afterwards.payment_state_updated_at,
        initiator=EventUser.from_user(shop_order_admin),
        order_id=placed_order.id,
        order_number=placed_order.order_number,
        orderer=EventUser.from_user(orderer_user),
    )
    order_canceled_signal_send_mock.assert_called_once_with(None, event=event)


@patch('byceps.signals.shop.order_paid.send')
@patch('byceps.blueprints.admin.shop.order.views.order_email_service')
def test_mark_order_as_paid(
    order_email_service_mock,
    order_paid_signal_send_mock,
    storefront: Storefront,
    shop_order_admin: User,
    orderer_user: User,
    orderer: Orderer,
    shop_order_admin_client,
):
    placed_order = place_order(storefront, orderer, [])
    db_order_before = get_db_order(placed_order.id)

    assert_payment_is_open(db_order_before)

    url = f'{BASE_URL}/shop/orders/{db_order_before.id}/mark_as_paid'
    form_data = {'payment_method': 'direct_debit'}
    response = shop_order_admin_client.post(url, data=form_data)

    db_order_afterwards = get_db_order(db_order_before.id)
    assert response.status_code == 302
    assert_payment(
        db_order_afterwards,
        'direct_debit',
        PaymentState.paid,
        shop_order_admin.id,
    )

    order_afterwards = order_service.get_order(placed_order.id)

    order_email_service_mock.send_email_for_paid_order_to_orderer.assert_called_once_with(
        order_afterwards
    )

    event = ShopOrderPaidEvent(
        occurred_at=db_order_afterwards.payment_state_updated_at,
        initiator=EventUser.from_user(shop_order_admin),
        order_id=placed_order.id,
        order_number=placed_order.order_number,
        orderer=EventUser.from_user(orderer_user),
        payment_method='direct_debit',
    )
    order_paid_signal_send_mock.assert_called_once_with(None, event=event)


@patch('byceps.signals.shop.order_canceled.send')
@patch('byceps.signals.shop.order_paid.send')
@patch('byceps.blueprints.admin.shop.order.views.order_email_service')
def test_cancel_after_paid(
    order_email_service_mock,
    order_paid_signal_send_mock,
    order_canceled_signal_send_mock,
    storefront: Storefront,
    article3: Article,
    shop_order_admin: User,
    orderer_user: User,
    orderer: Orderer,
    shop_order_admin_client,
):
    article = article3

    quantified_articles_to_order = [(article, 3)]
    placed_order = place_order(
        storefront, orderer, quantified_articles_to_order
    )
    db_order_before = get_db_order(placed_order.id)

    assert get_article_quantity(article.id) == 5

    assert_payment_is_open(db_order_before)

    url = f'{BASE_URL}/shop/orders/{db_order_before.id}/mark_as_paid'
    form_data = {'payment_method': 'bank_transfer'}
    response = shop_order_admin_client.post(url, data=form_data)

    url = f'{BASE_URL}/shop/orders/{db_order_before.id}/cancel'
    form_data = {
        'reason': 'Dein Vorname ist albern!',
        'send_email': 'n',
    }
    response = shop_order_admin_client.post(url, data=form_data)

    db_order_afterwards = get_db_order(db_order_before.id)
    assert response.status_code == 302
    assert_payment(
        db_order_afterwards,
        'bank_transfer',
        PaymentState.canceled_after_paid,
        shop_order_admin.id,
    )

    assert get_article_quantity(article.id) == 8

    order_afterwards = order_service.get_order(placed_order.id)

    order_email_service_mock.send_email_for_canceled_order_to_orderer.assert_called_once_with(
        order_afterwards
    )

    event = ShopOrderCanceledEvent(
        occurred_at=db_order_afterwards.payment_state_updated_at,
        initiator=EventUser.from_user(shop_order_admin),
        order_id=placed_order.id,
        order_number=placed_order.order_number,
        orderer=EventUser.from_user(orderer_user),
    )
    order_canceled_signal_send_mock.assert_called_once_with(None, event=event)


# helpers


def get_article_quantity(article_id: ArticleID) -> int:
    article = article_service.get_article(article_id)
    return article.quantity


def place_order(
    storefront: Storefront,
    orderer: Orderer,
    quantified_articles: Iterable[tuple[Article, int]],
) -> Order:
    cart = Cart(EUR)

    for article, quantity_to_order in quantified_articles:
        cart.add_item(article, quantity_to_order)

    order, _ = order_checkout_service.place_order(
        storefront, orderer, cart
    ).unwrap()

    return order


def assert_payment_is_open(db_order: DbOrder) -> None:
    assert db_order.payment_method is None  # default
    assert db_order.payment_state == PaymentState.open
    assert db_order.payment_state_updated_at is None
    assert db_order.payment_state_updated_by_id is None


def assert_payment(
    db_order: DbOrder,
    method: str | None,
    state: PaymentState,
    updated_by_id: UserID,
) -> None:
    assert db_order.payment_method == method
    assert db_order.payment_state == state
    assert db_order.payment_state_updated_at is not None
    assert db_order.payment_state_updated_by_id == updated_by_id


def get_db_order(order_id: OrderID) -> DbOrder:
    return db.session.get(DbOrder, order_id)
