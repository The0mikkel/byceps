"""
byceps.services.shop.order.models.action
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from byceps.services.shop.article.models import ArticleID

from .order import PaymentState


ActionParameters = dict[str, Any]


@dataclass(frozen=True)
class Action:
    id: UUID
    article_id: ArticleID
    payment_state: PaymentState
    procedure_name: str
    parameters: ActionParameters
