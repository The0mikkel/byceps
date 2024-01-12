"""
byceps.signals.shop
~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from blinker import Namespace


shop_signals = Namespace()


order_placed = shop_signals.signal('order-placed')
order_canceled = shop_signals.signal('order-canceled')
order_paid = shop_signals.signal('order-paid')
