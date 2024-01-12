"""
byceps.permissions.guest_server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from flask_babel import lazy_gettext

from byceps.util.authz import register_permissions


register_permissions(
    'guest_server',
    [
        ('administrate', lazy_gettext('Administrate guest servers')),
        ('view', lazy_gettext('View guest servers')),
    ],
)
