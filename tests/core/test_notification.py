import dataclasses

import pytest

from notifications.core.errors import ErrorCode, InvalidEventError
from notifications.core.notification import Category, Notification


def test_notification_identifies_recipient_category_event_type_and_message():
    n = Notification(
        recipient_id=1,
        category=Category.GAME,
        event_type="level_up",
        message="Congratulations! You've reached level 15!",
    )
    assert (n.recipient_id, n.category, n.event_type) == (1, Category.GAME, "level_up")
    assert "15" in n.message


def test_notification_is_immutable():
    n = Notification(1, Category.SOCIAL, "new_follower", "Alex is now following you.")
    with pytest.raises(dataclasses.FrozenInstanceError):
        n.message = "changed"  # type: ignore[misc]


def test_there_are_two_categories():
    assert {c.name for c in Category} == {"GAME", "SOCIAL"}


def test_invalid_event_error_carries_code_and_message_only():
    err = InvalidEventError(ErrorCode.MISSING_FIELD, "missing field 'new_level'")
    assert err.code is ErrorCode.MISSING_FIELD
    assert err.message == "missing field 'new_level'"
    assert str(err) == "missing field 'new_level'"
    assert not hasattr(err, "status_code")


def test_error_codes():
    assert {c.name for c in ErrorCode} == {
        "UNSUPPORTED_EVENT_TYPE",
        "MISSING_FIELD",
        "MALFORMED_FIELD",
        "SELF_TARGETED",
        "UNKNOWN_PLAYER",
    }
