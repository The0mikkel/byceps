"""
:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

import pytest

from byceps.services.news import news_channel_service, news_item_service
from byceps.services.news.models import BodyFormat
from byceps.services.site import site_service

from tests.helpers import create_site, http_client


SERVER_NAME = 'site-for-news.acmecon.test'

BASE_URL = f'http://{SERVER_NAME}'


@pytest.fixture(scope='module')
def editor(make_user):
    return make_user()


@pytest.fixture(scope='module')
def news_channel(brand):
    channel_id = f'{brand.id}-public'

    return news_channel_service.create_channel(brand, channel_id)


@pytest.fixture(scope='module')
def unpublished_news_item(news_channel, editor):
    slug = 'top-article'
    title = 'You will not believe this! [WIP]'
    body = 'Well, …'
    body_format = BodyFormat.html

    return news_item_service.create_item(
        news_channel, slug, editor, title, body, body_format
    )


@pytest.fixture(scope='module')
def published_news_item(news_channel, editor):
    slug = 'first-post'
    title = 'First Post!'
    body = 'Kann losgehen.'
    body_format = BodyFormat.html

    item = news_item_service.create_item(
        news_channel, slug, editor, title, body, body_format
    )
    news_item_service.publish_item(item.id).unwrap()
    return item


@pytest.fixture(scope='module')
def news_site(news_channel):
    site = create_site('newsflash', news_channel.brand_id)
    site_service.add_news_channel(site.id, news_channel.id)
    return site


@pytest.fixture(scope='module')
def news_site_app(make_site_app, news_site):
    return make_site_app(SERVER_NAME, news_site.id)


def test_view_news_frontpage(news_site_app):
    with http_client(news_site_app) as client:
        response = client.get(f'{BASE_URL}/news/')

    assert response.status_code == 200


def test_view_single_published_news_item(news_site_app, published_news_item):
    with http_client(news_site_app) as client:
        response = client.get(f'{BASE_URL}/news/{published_news_item.slug}')

    assert response.status_code == 200


def test_view_single_unpublished_news_item(
    news_site_app, unpublished_news_item
):
    with http_client(news_site_app) as client:
        response = client.get(f'{BASE_URL}/news/{unpublished_news_item.slug}')

    assert response.status_code == 404
