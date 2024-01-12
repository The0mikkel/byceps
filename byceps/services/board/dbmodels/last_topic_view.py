"""
byceps.services.board.dbmodels.last_topic_view
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship

from byceps.database import db
from byceps.services.board.models import TopicID
from byceps.services.user.models.user import UserID
from byceps.util.instances import ReprBuilder

from .topic import DbTopic


class DbLastTopicView(db.Model):
    """The last time a user looked into specific topic."""

    __tablename__ = 'board_topics_lastviews'

    user_id: Mapped[UserID] = mapped_column(
        db.Uuid, db.ForeignKey('users.id'), primary_key=True
    )
    topic_id: Mapped[TopicID] = mapped_column(
        db.Uuid, db.ForeignKey('board_topics.id'), primary_key=True
    )
    topic: Mapped[DbTopic] = relationship(DbTopic)
    occurred_at: Mapped[datetime]

    def __init__(
        self, user_id: UserID, topic_id: TopicID, occurred_at: datetime
    ) -> None:
        self.user_id = user_id
        self.topic_id = topic_id
        self.occurred_at = occurred_at

    def __repr__(self) -> str:
        return (
            ReprBuilder(self)
            .add_with_lookup('user_id')
            .add('topic', self.topic.title)
            .add_with_lookup('occurred_at')
            .build()
        )
