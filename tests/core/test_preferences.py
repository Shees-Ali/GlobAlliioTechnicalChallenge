"""Changing preferences through PreferenceService (feature 002)."""

import pytest

from fakes import new_id

from notifications.core.errors import ErrorCode, InvalidPreferenceError
from notifications.core.notification import Category
from notifications.core.service import Outcome


def level_up(player_id: int = 1, event_id: str | None = None) -> dict:
    return {"event_id": event_id or new_id(), "type": "level_up", "player_id": player_id, "new_level": 15}


def test_a_valid_change_is_applied(preference_service, preferences):  # FR-33
    preference_service.change({"player_id": 1, "category": "game", "enabled": False})
    assert preferences.get(1) == {Category.GAME: False}


def test_the_next_event_follows_the_change(preference_service, service, delivery):  # FR-33
    preference_service.change({"player_id": 1, "category": "game", "enabled": False})
    assert service.handle_event(level_up()) is Outcome.SUPPRESSED
    assert delivery.calls == []


def test_turning_a_category_back_on_does_not_replay_and_delivers_only_new_events(
    preference_service, service, delivery
):  # AC-35
    preference_service.change({"player_id": 1, "category": "game", "enabled": False})
    service.handle_event(level_up())

    preference_service.change({"player_id": 1, "category": "game", "enabled": True})
    assert delivery.calls == []  # the suppressed event is not replayed

    assert service.handle_event(level_up()) is Outcome.PROCESSED
    assert len(delivery.calls) == 1


def test_changing_one_category_leaves_the_other_as_it_was(preference_service, service):  # AC-36
    preference_service.change({"player_id": 1, "category": "game", "enabled": False})
    preference_service.change({"player_id": 1, "category": "social", "enabled": False})
    preference_service.change({"player_id": 1, "category": "social", "enabled": True})

    assert service.handle_event(level_up()) is Outcome.SUPPRESSED


def test_turning_off_a_category_twice_succeeds(preference_service, preferences):
    preference_service.change({"player_id": 1, "category": "game", "enabled": False})
    preference_service.change({"player_id": 1, "category": "game", "enabled": False})
    assert preferences.get(1) == {Category.GAME: False}


@pytest.mark.parametrize(
    ("payload", "code"),
    [
        ({"player_id": 99, "category": "game", "enabled": False}, ErrorCode.UNKNOWN_PLAYER),
        ({"player_id": 1, "category": "pvp", "enabled": False}, ErrorCode.UNSUPPORTED_CATEGORY),
        ({"player_id": 1, "category": 1, "enabled": False}, ErrorCode.UNSUPPORTED_CATEGORY),
        ({"player_id": 1, "category": "game", "enabled": 1}, ErrorCode.MALFORMED_FIELD),
        ({"player_id": 1, "category": "game", "enabled": "false"}, ErrorCode.MALFORMED_FIELD),
        ({"player_id": "1", "category": "game", "enabled": False}, ErrorCode.MALFORMED_FIELD),
        ({"player_id": True, "category": "game", "enabled": False}, ErrorCode.MALFORMED_FIELD),
        ({"category": "game", "enabled": False}, ErrorCode.MISSING_FIELD),
        ({"player_id": 1, "enabled": False}, ErrorCode.MISSING_FIELD),
        ({"player_id": 1, "category": "game"}, ErrorCode.MISSING_FIELD),
        ({"player_id": 1, "category": "game", "enabled": False, "x": 1}, ErrorCode.MALFORMED_FIELD),
        (["player_id", 1], ErrorCode.MALFORMED_FIELD),
    ],
)
def test_a_bad_change_is_rejected_and_changes_nothing(preference_service, preferences, payload, code):  # AC-37
    preferences.set(1, Category.GAME, True)

    with pytest.raises(InvalidPreferenceError) as error:
        preference_service.change(payload)

    assert error.value.code is code
    assert error.value.message
    assert preferences.get(1) == {Category.GAME: True}
    assert preferences.get(99) == {}
