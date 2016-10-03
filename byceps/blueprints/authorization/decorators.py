# -*- coding: utf-8 -*-

"""
byceps.blueprints.authorization.decorators
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2016 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from functools import wraps

from flask import abort, g


def permission_required(permission):
    """Ensure the current user has the given permission."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if permission not in g.current_user.permissions:
                abort(403)
            return func(*args, **kwargs)
        return wrapper
    return decorator
