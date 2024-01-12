"""
byceps.util.l10n
~~~~~~~~~~~~~~~~

Localization.

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from collections.abc import Iterator
from contextlib import contextmanager

from babel import Locale
from flask import current_app, g, request
from flask_babel import force_locale, format_currency, get_locale
from moneyed import Money
from wtforms import Form

from byceps.services.user.models.user import User


def get_current_user_locale() -> str | None:
    """Return the locale for the current user, if available."""
    # Look for a locale on the current user object.
    user = g.user
    if (user is not None) and (user.locale is not None):
        return user.locale

    if request:
        # Try to match user agent's accepted languages.
        languages = [locale.language for locale in g.locales]
        return request.accept_languages.best_match(languages)

    return None


@contextmanager
def force_user_locale(user: User) -> Iterator[None]:
    """Execute code with the user's preferred locale."""
    locale = get_user_locale(user)
    with force_locale(locale):
        yield


def get_default_locale() -> str:
    """Return the application's default locale."""
    return current_app.config['LOCALE']


def get_user_locale(user: User) -> str:
    """Return the user's preferred locale.

    If no preference is set for the user, return the app's default
    locale.
    """
    return user.locale or get_default_locale()


BASE_LOCALE = Locale('en')


def get_locales() -> list[Locale]:
    """List available locales."""
    return [BASE_LOCALE] + current_app.babel_instance.list_translations()


def get_locale_str() -> str | None:
    """Return the current locale as a string.

    Return `None` outside of a request.
    """
    locale = get_locale()
    if locale is None:
        return None

    locale_str = locale.language
    if locale.territory:
        locale_str += '_' + locale.territory

    return locale_str


class LocalizedForm(Form):
    def __init__(self, *args, **kwargs):
        locales = current_app.config['LOCALES_FORMS']
        kwargs['meta'] = {'locales': locales}
        super().__init__(*args, **kwargs)


def format_money(money: Money) -> str:
    """Format monetary value with amount and currency."""
    return format_currency(money.amount, money.currency.code)
