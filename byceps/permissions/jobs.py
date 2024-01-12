"""
byceps.permissions.jobs
~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from flask_babel import lazy_gettext

from byceps.util.authz import register_permissions


register_permissions(
    'jobs',
    [
        ('view', lazy_gettext('View jobs')),
    ],
)
