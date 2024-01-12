"""
:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from byceps.services.news import news_channel_service


BASE_URL = 'http://admin.acmecon.test'


def test_index_for_brand(news_admin_client, brand, channel):
    url = f'{BASE_URL}/news/brands/{brand.id}'
    response = news_admin_client.get(url)
    assert response.status_code == 200


def test_view(news_admin_client, channel):
    url = f'{BASE_URL}/news/channels/{channel.id}'
    response = news_admin_client.get(url)
    assert response.status_code == 200


def test_create_form(news_admin_client, brand):
    url = f'{BASE_URL}/news/for_brand/{brand.id}/channels/create'
    response = news_admin_client.get(url)
    assert response.status_code == 200


def test_create(news_admin_client, brand, site):
    channel_id = 'test-channel-2'
    announcement_site_id = site.id

    assert news_channel_service.find_channel(channel_id) is None

    url = f'{BASE_URL}/news/for_brand/{brand.id}/channels'
    form_data = {
        'channel_id': channel_id,
        'announcement_site_id': str(announcement_site_id),
    }
    response = news_admin_client.post(url, data=form_data)
    assert response.status_code == 302

    channel = news_channel_service.find_channel(channel_id)
    assert channel is not None
    assert channel.id == channel_id
    assert channel.brand_id == brand.id
    assert channel.announcement_site_id == announcement_site_id
