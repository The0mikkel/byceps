"""
byceps.services.board.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import NewType
from uuid import UUID

from byceps.services.brand.models import BrandID
from byceps.services.user.models.user import User, UserID


BoardID = NewType('BoardID', str)


BoardCategoryID = NewType('BoardCategoryID', UUID)


PostingID = NewType('PostingID', UUID)


TopicID = NewType('TopicID', UUID)


@dataclass(frozen=True)
class Board:
    id: BoardID
    brand_id: BrandID
    access_restricted: bool


@dataclass(frozen=True)
class BoardCategory:
    id: BoardCategoryID
    board_id: BoardID
    position: int
    slug: str
    title: str
    description: str
    topic_count: int
    posting_count: int
    hidden: bool


@dataclass(frozen=True)
class BoardCategoryWithLastUpdate(BoardCategory):
    last_posting_updated_at: datetime
    last_posting_updated_by: User


@dataclass(frozen=True)
class PostingReaction:
    id: UUID
    created_at: datetime
    posting_id: PostingID
    user_id: UserID
    kind: str


@dataclass(frozen=True)
class PostingReactionUser:
    id: UserID
    screen_name: str | None
