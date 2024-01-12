"""
:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from byceps.services.news import news_item_service


BASE_URL = 'http://admin.acmecon.test'


def test_view(news_admin_client, item):
    url = f'{BASE_URL}/news/items/{item.id}'
    response = news_admin_client.get(url)
    assert response.status_code == 200


def test_view_version(news_admin_client, item):
    version = news_item_service.get_current_item_version(item.id)
    url = f'{BASE_URL}/news/versions/{version.id}'
    response = news_admin_client.get(url)
    assert response.status_code == 200


def test_list_versions(news_admin_client, item):
    url = f'{BASE_URL}/news/items/{item.id}/versions'
    response = news_admin_client.get(url)
    assert response.status_code == 200


def test_compare_versions(news_admin_client, item):
    version = news_item_service.get_current_item_version(item.id)
    url = f'{BASE_URL}/news/items/{version.id}/compare_to/{version.id}'
    response = news_admin_client.get(url)
    assert response.status_code == 200


def test_create_form(news_admin_client, channel):
    url = f'{BASE_URL}/news/for_channel/{channel.id}/create'
    response = news_admin_client.get(url)
    assert response.status_code == 200


def test_create(news_admin_client, channel, news_admin):
    slug = 'what-a-blast'
    title = 'Wow, That Party was a Blast!'
    body = 'So many cool memories.'

    url = f'{BASE_URL}/news/for_channel/{channel.id}'
    form_data = {
        'slug': slug,
        'title': title,
        'body_format': 'html',
        'body': body,
    }
    response = news_admin_client.post(url, data=form_data)

    location = response.headers['Location']
    item_id = location.rpartition('/')[-1]

    item = news_item_service.find_item(item_id)
    assert item is not None
    assert item.id is not None
    assert item.channel.id == channel.id
    assert item.slug == slug
    assert item.published_at is None
    assert not item.published
    assert item.title == title
    assert item.body == body
    assert item.images == []


def test_update_form(news_admin_client, item):
    url = f'{BASE_URL}/news/items/{item.id}/update'
    response = news_admin_client.get(url)
    assert response.status_code == 200


def test_publish_later_form(news_admin_client, item):
    url = f'{BASE_URL}/news/items/{item.id}/publish_later'
    response = news_admin_client.get(url)
    assert response.status_code == 200


def test_publish_later(news_admin_client, item):
    item_before = news_item_service.find_item(item.id)
    assert item_before.published_at is None
    assert not item_before.published

    url = f'{BASE_URL}/news/items/{item.id}/publish_later'
    form_data = {
        'publish_on': '2021-01-23',
        'publish_at': '23:42',
    }
    response = news_admin_client.post(url, data=form_data)
    assert response.status_code == 302

    item_after = news_item_service.find_item(item.id)
    assert item_after.published_at is not None
    assert item_after.published


def test_publish_now(news_admin_client, item):
    item_before = news_item_service.find_item(item.id)
    assert item_before.published_at is None
    assert not item_before.published

    url = f'{BASE_URL}/news/items/{item.id}/publish_now'
    response = news_admin_client.post(url)
    assert response.status_code == 204

    item_after = news_item_service.find_item(item.id)
    assert item_after.published_at is not None
    assert item_after.published


def test_unpublish(news_admin_client, item):
    news_item_service.publish_item(item.id).unwrap()

    item_before = news_item_service.find_item(item.id)
    assert item_before.published_at is not None
    assert item_before.published

    url = f'{BASE_URL}/news/items/{item.id}/unpublish'
    response = news_admin_client.post(url)
    assert response.status_code == 204

    item_after = news_item_service.find_item(item.id)
    assert item_after.published_at is None
    assert not item_after.published
