# -*- coding: utf-8 -*-

"""
byceps.config
~~~~~~~~~~~~~

:Copyright: 2006-2014 Jochen Kupperschmidt
"""

from enum import Enum

from flask import current_app


EXTENSION_KEY = 'byceps'
KEY_SITE_MODE = 'site_mode'
KEY_PARTY_ID = 'party_id'


SiteMode = Enum('SiteMode', ['public', 'admin'])
SiteMode.is_admin = lambda self: self == SiteMode.admin
SiteMode.is_public = lambda self: self == SiteMode.public


def init_app(app):
    app.extensions[EXTENSION_KEY] = {}

    site_mode = determine_site_mode(app)
    app.extensions[EXTENSION_KEY][KEY_SITE_MODE] = site_mode

    if site_mode.is_public():
        party_id = determine_party_id(app)
        app.extensions[EXTENSION_KEY][KEY_PARTY_ID] = party_id


def determine_site_mode(app):
    value = app.config.get('MODE')
    if value is None:
        raise Exception('No site mode configured.')

    try:
        return SiteMode[value]
    except KeyError:
        raise Exception('Invalid site mode "{}" configured.'.format(value))


def get_site_mode(app=None):
    """Return the mode the site should run in."""
    return _get_config_dict(app)[KEY_SITE_MODE]


def determine_party_id(app):
    party_id = app.config.get('PARTY')
    if party_id is None:
        raise Exception('No party configured.')

    return party_id


def get_current_party_id(app=None):
    """Return the id of the current party."""
    return _get_config_dict(app)[KEY_PARTY_ID]


def _get_config_dict(app=None):
    if app is None:
        app = current_app

    return app.extensions[EXTENSION_KEY]
