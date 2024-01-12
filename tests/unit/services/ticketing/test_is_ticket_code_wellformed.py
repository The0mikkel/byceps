"""
:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

import pytest

from byceps.services.ticketing import ticket_code_service


# fmt: off
@pytest.mark.parametrize(
    ('code', 'expected'),
    [
        ('ZWXL'  , False),  # denied: too short
        ('zwxln' , False),  # denied: not all-uppercase
        ('ZWXLN' , True ),  # okay
        ('ZW2LN' , True ),  # okay: numbers are fine (but can be hard to distinguish)
        ('ZAXLN' , True ),  # okay (even though vowels are not in alphabet; all uppercase ASCII letters are fine)
        ('ZÄXLN' , False),  # denied: umlaut is not in alphabet
        ('ZWXLNG', False),  # denied: too long
    ],
)
# fmt: on
def test_is_ticket_code_wellformed(code, expected):
    assert ticket_code_service.is_ticket_code_wellformed(code) == expected
