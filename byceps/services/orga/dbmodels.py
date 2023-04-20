"""
byceps.services.orga.dbmodels
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from byceps.database import db
from byceps.services.brand.dbmodels.brand import DbBrand
from byceps.services.user.dbmodels.user import DbUser
from byceps.typing import BrandID, UserID
from byceps.util.instances import ReprBuilder


class DbOrgaFlag(db.Model):
    """A user's organizer status for a single brand."""

    __tablename__ = 'orga_flags'

    brand_id = db.Column(
        db.UnicodeText, db.ForeignKey('brands.id'), primary_key=True
    )
    brand = db.relationship(DbBrand)
    user_id = db.Column(db.Uuid, db.ForeignKey('users.id'), primary_key=True)
    user = db.relationship(DbUser)

    def __init__(self, brand_id: BrandID, user_id: UserID) -> None:
        self.brand_id = brand_id
        self.user_id = user_id

    def __repr__(self) -> str:
        return (
            ReprBuilder(self)
            .add('brand', self.brand_id)
            .add('user', self.user.screen_name)
            .build()
        )
