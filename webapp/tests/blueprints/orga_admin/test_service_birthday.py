# -*- coding: utf-8 -*-

"""
:Copyright: 2006-2015 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from datetime import date
from unittest import TestCase

from freezegun import freeze_time
from nose2.tools import params

from byceps.blueprints.orga_admin.service import sort_users_by_next_birthday

from testfixtures.user import create_user_with_detail


class BirthdayListTestCase(TestCase):

    @freeze_time('1994-09-30')
    def test_sort(self):
        born1985 = create_user(date(1985,  9, 29))
        born1987 = create_user(date(1987, 10,  1))
        born1991 = create_user(date(1991, 11, 14))
        born1992 = create_user(date(1992, 11, 14))
        born1994 = create_user(date(1994,  9, 30))

        users = [
            born1994,
            born1992,
            born1985,
            born1991,
            born1987,
        ]

        expected = [
            born1994,
            born1987,
            born1991,
            born1992,
            born1985,
        ]

        actual = list(sort_users_by_next_birthday(users))
        self.assertEquals(actual, expected)


def create_user(date_of_birth):
    return create_user_with_detail(42, date_of_birth=date_of_birth)
