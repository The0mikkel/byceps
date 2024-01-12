"""
:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from byceps.services.user_badge import user_badge_service


BASE_URL = 'http://admin.acmecon.test'


def test_index(user_badge_admin_client):
    url = f'{BASE_URL}/user_badges/badges'
    response = user_badge_admin_client.get(url)
    assert response.status_code == 200


def test_view(user_badge_admin_client, badge):
    url = f'{BASE_URL}/user_badges/badges/{badge.id}'
    response = user_badge_admin_client.get(url)
    assert response.status_code == 200


def test_create_form(user_badge_admin_client):
    url = f'{BASE_URL}/user_badges/create'
    response = user_badge_admin_client.get(url)
    assert response.status_code == 200


def test_create(user_badge_admin_client, brand):
    slug = 'seal-of-resilience'
    label = 'Seal of Resilience'
    image_filename = 'seal-of-resilience.svg'
    description = 'Stay put, get this.'

    assert user_badge_service.find_badge_by_slug(slug) is None

    url = f'{BASE_URL}/user_badges/badges'
    form_data = {
        'slug': slug,
        'label': label,
        'image_filename': image_filename,
        'description': description,
        'brand_id': brand.id,
        'featured': 'Y',
    }
    response = user_badge_admin_client.post(url, data=form_data)
    assert response.status_code == 302

    badge = user_badge_service.find_badge_by_slug(slug)
    assert badge is not None
    assert badge.id is not None
    assert badge.slug == slug
    assert badge.label == label
    assert badge.image_filename == image_filename
    assert badge.description == description
    assert badge.brand_id == brand.id
    assert badge.featured


def test_update_form(user_badge_admin_client, badge):
    url = f'{BASE_URL}/user_badges/badges/{badge.id}/update'
    response = user_badge_admin_client.get(url)
    assert response.status_code == 200
