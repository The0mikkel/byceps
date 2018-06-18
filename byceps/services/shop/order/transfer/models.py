"""
byceps.services.shop.order.transfer.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2018 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from decimal import Decimal
from typing import NewType
from uuid import UUID

from attr import attrib, attrs

from ...article.transfer.models import ArticleNumber


OrderID = NewType('OrderID', UUID)


OrderNumber = NewType('OrderNumber', str)


@attrs(frozen=True, slots=True)
class OrderItem:
    order_number = attrib(type=OrderNumber)
    article_number = attrib(type=ArticleNumber)
    description = attrib(type=str)
    unit_price = attrib(type=Decimal)
    tax_rate = attrib(type=Decimal)
    quantity = attrib(type=int)
    line_price = attrib(type=Decimal)
