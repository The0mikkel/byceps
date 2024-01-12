"""
byceps.services.shop.shipping.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from dataclasses import dataclass

from byceps.services.shop.article.models import ArticleID


@dataclass(frozen=True)
class ArticleToShip:
    article_id: ArticleID
    description: str
    quantity_paid: int
    quantity_open: int
    quantity_total: int
