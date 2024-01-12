"""
:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from datetime import datetime

from byceps.util.datetime.range import DateTimeRange


def test_range_repr():
    dtr = DateTimeRange(
        datetime(2014, 8, 15, 19, 30, 0),
        datetime(2014, 8, 16, 7, 2, 34),
    )

    assert repr(dtr) == '[2014-08-15 19:30:00..2014-08-16 07:02:34)'
