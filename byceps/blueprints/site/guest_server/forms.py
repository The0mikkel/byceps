"""
byceps.blueprints.site.guest_server.forms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

import re

from flask_babel import lazy_gettext
from wtforms import StringField, TextAreaField
from wtforms.validators import InputRequired, Length, Optional, Regexp

from byceps.util.l10n import LocalizedForm


HOSTNAME_REGEX = re.compile('^[A-Za-z][A-Za-z0-9-]+$')


class RegisterForm(LocalizedForm):
    hostname = StringField(
        lazy_gettext('Hostname'),
        validators=[InputRequired(), Length(max=20), Regexp(HOSTNAME_REGEX)],
    )
    description = StringField(
        lazy_gettext('Description'), validators=[Optional(), Length(max=100)]
    )
    notes = TextAreaField(
        lazy_gettext('Notes'), validators=[Optional(), Length(max=1000)]
    )
