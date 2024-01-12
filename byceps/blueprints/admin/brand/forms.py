"""
byceps.blueprints.admin.brand.forms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from flask_babel import lazy_gettext
from wtforms import BooleanField, StringField
from wtforms.validators import InputRequired, Length, Optional, ValidationError

from byceps.services.brand import brand_service
from byceps.util.l10n import LocalizedForm


class _BaseForm(LocalizedForm):
    title = StringField(
        lazy_gettext('Title'),
        validators=[InputRequired(), Length(min=1, max=40)],
    )


class CreateForm(_BaseForm):
    id = StringField(
        lazy_gettext('ID'), validators=[InputRequired(), Length(min=1, max=20)]
    )

    @staticmethod
    def validate_id(form, field):
        brand_id = field.data
        if brand_service.find_brand(brand_id) is not None:
            raise ValidationError(lazy_gettext('The value is already in use.'))


class UpdateForm(_BaseForm):
    image_filename = StringField(
        lazy_gettext('Image filename'), validators=[Optional()]
    )
    archived = BooleanField(lazy_gettext('archived'))


class EmailConfigUpdateForm(LocalizedForm):
    sender_address = StringField(
        lazy_gettext('Sender address'), validators=[InputRequired()]
    )
    sender_name = StringField(
        lazy_gettext('Sender name'), validators=[Optional()]
    )
    contact_address = StringField(
        lazy_gettext('Contact address'), validators=[Optional()]
    )
