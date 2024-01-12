"""
:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

import pytest

from byceps.services.user import (
    user_command_service,
    user_log_service,
    user_service,
)


@pytest.fixture(scope='module')
def admin_user(make_user):
    return make_user()


@pytest.fixture()
def cheater(make_user):
    return make_user()


@pytest.fixture()
def remorseful_user(make_user):
    return make_user()


def test_suspend(admin_app, cheater, admin_user):
    user = cheater

    reason = 'User has been caught cheating.'

    user_before = user_service.get_user(user.id)
    assert not user_before.suspended

    log_entries_before = user_log_service.get_entries_for_user(user_before.id)
    assert len(log_entries_before) == 2  # user creation

    # -------------------------------- #

    user_command_service.suspend_account(user, admin_user, reason)

    # -------------------------------- #

    user_after = user_service.get_user(user.id)
    assert user_after.suspended

    log_entries_after = user_log_service.get_entries_for_user(user_after.id)
    assert len(log_entries_after) == 3

    suspended_log_entry = log_entries_after[-1]
    assert suspended_log_entry.event_type == 'user-suspended'
    assert suspended_log_entry.data == {
        'initiator_id': str(admin_user.id),
        'reason': reason,
    }


def test_unsuspend(admin_app, remorseful_user, admin_user):
    user = remorseful_user

    user_command_service.suspend_account(user, admin_user, 'Annoying')

    reason = 'User showed penitence. Drop the ban.'

    user_before = user_service.get_user(user.id)
    assert user_before.suspended

    log_entries_before = user_log_service.get_entries_for_user(user_before.id)
    assert len(log_entries_before) == 3

    # -------------------------------- #

    user_command_service.unsuspend_account(user, admin_user, reason)

    # -------------------------------- #

    user_after = user_service.get_user(user.id)
    assert not user_after.suspended

    log_entries_after = user_log_service.get_entries_for_user(user_after.id)
    assert len(log_entries_after) == 4

    unsuspended_log_entry = log_entries_after[-1]
    assert unsuspended_log_entry.event_type == 'user-unsuspended'
    assert unsuspended_log_entry.data == {
        'initiator_id': str(admin_user.id),
        'reason': reason,
    }
