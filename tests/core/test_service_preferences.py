"""The preference check inside handle_event (feature 002)."""

import pytest

from fakes import new_id

from notifications.core.errors import ErrorCode, InvalidEventError
from notifications.core.events import REGISTRY
from notifications.core.notification import Category
from notifications.core.service import NotificationService, Outcome

# One builder per event type, each with player 1 as the recipient and a fresh event ID.
TO_PLAYER_1 = {
    "level_up": lambda: {"event_id": new_id(), "type": "level_up", "player_id": 1, "new_level": 15},
    "item_acquired": lambda: {"event_id": new_id(), "type": "item_acquired", "player_id": 1, "item_name": "SwordOfAzeroth"},
    "challenge_completed": lambda: {"event_id": new_id(), "type": "challenge_completed", "player_id": 1, "challenge_name": "Quest"},
    "friend_request": lambda: {"event_id": new_id(), "type": "friend_request", "requester_id": 3, "recipient_id": 1},
    "friend_accepted": lambda: {"event_id": new_id(), "type": "friend_accepted", "accepter_id": 3, "requester_id": 1},
    "new_follower": lambda: {"event_id": new_id(), "type": "new_follower", "follower_id": 3, "followed_id": 1},
}


def test_every_registered_type_has_a_builder():
    assert sorted(TO_PLAYER_1) == sorted(REGISTRY)


@pytest.mark.parametrize("event_type", sorted(REGISTRY))
def test_with_no_recorded_preferences_every_event_type_is_delivered(service, delivery, event_type):  # AC-29
    assert service.handle_event(TO_PLAYER_1[event_type]()) is Outcome.PROCESSED
    assert len(delivery.calls) == 1
    assert delivery.calls[0][0].recipient_id == 1


def test_a_disabled_category_is_suppressed_and_not_delivered(service, delivery, preferences):  # AC-27
    preferences.set(1, Category.GAME, False)

    assert service.handle_event(TO_PLAYER_1["level_up"]()) is Outcome.SUPPRESSED
    assert delivery.calls == []


def test_a_disabled_category_does_not_affect_the_other_category(service, delivery, preferences):  # AC-28
    preferences.set(1, Category.GAME, False)

    assert service.handle_event(TO_PLAYER_1["friend_request"]()) is Outcome.PROCESSED
    assert len(delivery.calls) == 1


@pytest.mark.parametrize("event_type", sorted(REGISTRY))
def test_every_type_in_a_disabled_category_is_suppressed(service, delivery, preferences, event_type):  # AC-27
    category = REGISTRY[event_type].category
    preferences.set(1, category, False)

    assert service.handle_event(TO_PLAYER_1[event_type]()) is Outcome.SUPPRESSED
    assert delivery.calls == []


def test_one_players_setting_does_not_affect_another_player(service, delivery, preferences):  # AC-30
    preferences.set(1, Category.GAME, False)

    event = {"event_id": new_id(), "type": "level_up", "player_id": 2, "new_level": 3}
    assert service.handle_event(event) is Outcome.PROCESSED
    assert delivery.calls[0][0].recipient_id == 2


def test_only_the_recipients_preferences_are_checked(service, delivery, preferences):  # AC-31
    preferences.set(3, Category.SOCIAL, False)  # the sender has Social off, the recipient does not

    event = {"event_id": new_id(), "type": "friend_request", "requester_id": 3, "recipient_id": 1}
    assert service.handle_event(event) is Outcome.PROCESSED
    assert delivery.calls[0][0].recipient_id == 1


def test_an_invalid_event_is_rejected_not_suppressed(service, delivery, preferences):  # AC-33
    preferences.set(1, Category.GAME, False)

    with pytest.raises(InvalidEventError) as error:
        service.handle_event({"event_id": new_id(), "type": "level_up", "player_id": 1})
    assert error.value.code is ErrorCode.MISSING_FIELD
    assert delivery.calls == []


def test_an_unknown_actor_is_rejected_not_suppressed(service, delivery, preferences):  # AC-33
    preferences.set(1, Category.SOCIAL, False)

    with pytest.raises(InvalidEventError) as error:
        service.handle_event({"event_id": new_id(), "type": "friend_request", "requester_id": 99, "recipient_id": 1})
    assert error.value.code is ErrorCode.UNKNOWN_PLAYER
    assert delivery.calls == []


def test_a_suppressed_event_uses_up_its_id(service, delivery, preferences):  # AC-34
    event = TO_PLAYER_1["level_up"]()
    preferences.set(1, Category.GAME, False)
    assert service.handle_event(event) is Outcome.SUPPRESSED

    preferences.set(1, Category.GAME, True)
    assert service.handle_event(event) is Outcome.DUPLICATE
    assert delivery.calls == []


class FailingPreferenceStore:
    """A store that cannot be read, for its first `fail_times` reads."""

    def __init__(self, fail_times: int = 1) -> None:
        self.remaining_failures = fail_times

    def get(self, player_id):
        if self.remaining_failures > 0:
            self.remaining_failures -= 1
            raise ConnectionError("preference store is down")
        return {}

    def set(self, player_id, category, enabled):
        raise NotImplementedError


def test_a_failed_preference_read_releases_the_id(directory, delivery, processed_events):  # FR-22, FR-32
    service = NotificationService(directory, delivery, processed_events, FailingPreferenceStore())
    event = TO_PLAYER_1["level_up"]()

    with pytest.raises(ConnectionError):
        service.handle_event(event)  # the error reaches the submitter
    assert delivery.calls == []

    assert service.handle_event(event) is Outcome.PROCESSED  # the resend is not a duplicate
    assert len(delivery.calls) == 1
