"""
:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

import pytest

from byceps.services.email.models import NameAndAddress


# fmt: off
@pytest.mark.parametrize(
    ('name', 'address', 'expected'),
    [
        (None, 'unnamed@users.test', 'unnamed@users.test'),
        ('Simple', 'simple@users.test', 'Simple <simple@users.test>'),
        ('Mr. Pink', 'mr.pink@users.test', '"Mr. Pink" <mr.pink@users.test>'),  # quotes name
    ],
)
# fmt: on
def test_name_and_address_format(name, address, expected):
    name_and_address = NameAndAddress(name, address)
    assert name_and_address.format() == expected
