# -*- coding: utf-8 -*-

"""
:Copyright: 2006-2015 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from pathlib import Path
from unittest import TestCase

from nose2.tools import params

from byceps.util.image import Dimensions, guess_type, ImageType, read_dimensions


class ImageTestCase(TestCase):

    @params(
        ('bmp',  None          ),
        ('gif',  ImageType.gif ),
        ('jpeg', ImageType.jpeg),
        ('png',  ImageType.png ),
    )
    def test_guess_type(self, filename_suffix, expected):
        with open_image_with_suffix(filename_suffix) as f:
            actual = guess_type(f)

        self.assertEqual(actual, expected)

    @params(
        ('bmp',   7, 11),
        ('gif',  17,  4),
        ('jpeg', 12,  7),
        ('png',   8, 25),
    )
    def test_read_dimensions(self, filename_suffix, expected_width, expected_height):
        expected = Dimensions(width=expected_width, height=expected_height)

        with open_image_with_suffix(filename_suffix) as f:
            actual = read_dimensions(f)

        self.assertEqual(actual, expected)


def open_image_with_suffix(suffix):
    path = Path('testfixtures/images/image').with_suffix('.' + suffix)
    return path.open(mode='rb')
