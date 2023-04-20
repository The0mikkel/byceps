"""
byceps.blueprints.admin.snippet.forms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from flask_babel import lazy_gettext
from wtforms import SelectField, StringField, TextAreaField
from wtforms.validators import InputRequired

from byceps.services.language import language_service
from byceps.util.l10n import LocalizedForm


class CreateForm(LocalizedForm):
    name = StringField(lazy_gettext('Name'), [InputRequired()])
    language_code = SelectField(
        lazy_gettext('Language code'), [InputRequired()]
    )
    body = TextAreaField(lazy_gettext('Text'), [InputRequired()])

    def set_language_code_choices(self):
        languages = language_service.get_languages()
        choices = [(language.code, language.code) for language in languages]
        choices.sort()
        self.language_code.choices = choices


class UpdateForm(CreateForm):
    pass
