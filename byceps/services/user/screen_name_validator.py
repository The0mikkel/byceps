"""
byceps.services.user.screen_name_validator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Validate screen names regarding their contained characters

:Copyright: 2006-2019 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from itertools import chain
from string import ascii_letters, digits

MIN_LENGTH = 4
MAX_LENGTH = 24

GERMAN_CHARS = 'äöüß'
SPECIAL_CHARS = '!$&*-./<=>?[]_'

VALID_CHARS = frozenset(chain(
    ascii_letters, digits, GERMAN_CHARS, SPECIAL_CHARS))


def is_screen_name_valid(screen_name: str) -> bool:
    """Return `True` if the screen name contains only permitted characters."""
    if not MIN_LENGTH <= len(screen_name) <= MAX_LENGTH:
        return False

    return all(map(VALID_CHARS.__contains__, screen_name))
