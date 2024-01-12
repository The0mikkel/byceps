"""
:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from byceps.services.board import board_category_query_service


BASE_URL = 'http://admin.acmecon.test'


def test_create_form(board_admin_client, board):
    url = f'{BASE_URL}/boards/categories/for_board/{board.id}/create'
    response = board_admin_client.get(url)
    assert response.status_code == 200


def test_create(board_admin_client, board):
    slug = 'off-topic'
    title = 'Off-Topic'
    description = 'Random stuff'

    assert (
        board_category_query_service.find_category_by_slug(board.id, slug)
        is None
    )

    url = f'{BASE_URL}/boards/categories/for_board/{board.id}'
    form_data = {
        'slug': slug,
        'title': title,
        'description': description,
    }
    response = board_admin_client.post(url, data=form_data)
    assert response.status_code == 302

    category = board_category_query_service.find_category_by_slug(
        board.id, slug
    )
    assert category is not None
    assert category.id is not None
    assert category.slug == slug
    assert category.title == title
    assert category.description == description


def test_update_form(board_admin_client, category):
    url = f'{BASE_URL}/boards/categories/{category.id}/update'
    response = board_admin_client.get(url)
    assert response.status_code == 200
