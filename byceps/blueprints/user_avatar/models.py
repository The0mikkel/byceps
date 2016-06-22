# -*- coding: utf-8 -*-

"""
byceps.blueprints.user_avatar.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2016 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from collections import namedtuple
from datetime import datetime
from pathlib import Path

from flask import current_app, url_for
from sqlalchemy.ext.hybrid import hybrid_property

from ...database import db, generate_uuid
from ...util.image import ImageType
from ...util.instances import ReprBuilder


class Avatar(db.Model):
    """A user's avatar image."""
    __tablename__ = 'user_avatars'

    id = db.Column(db.Uuid, default=generate_uuid, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    creator_id = db.Column(db.Uuid, db.ForeignKey('users.id'), nullable=False)
    creator = db.relationship('User')
    _image_type = db.Column(db.Unicode(4), nullable=False)

    def __init__(self, creator, image_type):
        self.creator = creator
        self.image_type = image_type

    @hybrid_property
    def image_type(self):
        image_type_str = self._image_type
        if image_type_str is not None:
            return ImageType[image_type_str]

    @image_type.setter
    def image_type(self, image_type):
        self._image_type = image_type.name if (image_type is not None) else None

    @property
    def filename(self):
        timestamp = int(self.created_at.timestamp())
        name_without_suffix = '{}_{:d}'.format(self.creator.id, timestamp)
        suffix = '.' + self.image_type.name
        return Path(name_without_suffix).with_suffix(suffix)

    @property
    def path(self):
        path = current_app.config['PATH_USER_AVATAR_IMAGES']
        return path / self.filename

    @property
    def url(self):
        path = 'users/avatars/{}'.format(self.filename)
        return url_for('global_file', filename=path)

    def __repr__(self):
        return ReprBuilder(self) \
            .add_with_lookup('id') \
            .add('creator', self.creator.screen_name) \
            .add('image_type', self.image_type.name) \
            .build()
