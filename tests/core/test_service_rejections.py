import pytest

from fakes import new_id

from notifications.core.errors import ErrorCode, InvalidEventError
from notifications.core.service import NotificationService


@pytest.fixture
def service(directory, delivery) -> NotificationService:
    return NotificationService(directory, delivery)


def assert_rejected(service, delivery, payload, code):
    with pytest.raises(InvalidEventError) as info:
        service.handle_event(payload)
    assert info.value.code is code
    assert delivery.calls == []
    return info.value


@pytest.mark.parametrize(
    "payload",
    [
        {"event_id": new_id(), "type": "friend_request", "requester_id": 1, "recipient_id": 1},
        {"event_id": new_id(), "type": "friend_accepted", "accepter_id": 2, "requester_id": 2},
        {"event_id": new_id(), "type": "new_follower", "follower_id": 3, "followed_id": 3},
    ],
)
def test_a_self_targeted_social_event_is_rejected(service, delivery, payload):  # AC-14
    assert_rejected(service, delivery, payload, ErrorCode.SELF_TARGETED)


def test_a_self_targeted_event_is_rejected_before_any_lookup(service, delivery, directory):  # AC-14
    assert_rejected(
        service,
        delivery,
        {"event_id": new_id(), "type": "new_follower", "follower_id": 3, "followed_id": 3},
        ErrorCode.SELF_TARGETED,
    )
    assert directory.lookups == []


@pytest.mark.parametrize(
    "payload",
    [
        {"event_id": new_id(), "type": "level_up", "player_id": 99, "new_level": 5},
        {"event_id": new_id(), "type": "item_acquired", "player_id": 99, "item_name": "Sword"},
        {"event_id": new_id(), "type": "challenge_completed", "player_id": 99, "challenge_name": "Quest"},
    ],
)
def test_an_unknown_recipient_is_rejected_for_game_events(service, delivery, payload):  # AC-15
    err = assert_rejected(service, delivery, payload, ErrorCode.UNKNOWN_PLAYER)
    assert "99" in err.message


@pytest.mark.parametrize(
    "payload",
    [
        {"event_id": new_id(), "type": "friend_request", "requester_id": 3, "recipient_id": 99},
        {"event_id": new_id(), "type": "friend_accepted", "accepter_id": 1, "requester_id": 99},
        {"event_id": new_id(), "type": "new_follower", "follower_id": 4, "followed_id": 99},
    ],
)
def test_an_unknown_recipient_is_rejected_for_social_events(service, delivery, payload):  # AC-15
    err = assert_rejected(service, delivery, payload, ErrorCode.UNKNOWN_PLAYER)
    assert "99" in err.message


@pytest.mark.parametrize(
    "payload",
    [
        {"event_id": new_id(), "type": "friend_request", "requester_id": 99, "recipient_id": 1},
        {"event_id": new_id(), "type": "friend_accepted", "accepter_id": 99, "requester_id": 3},
        {"event_id": new_id(), "type": "new_follower", "follower_id": 99, "followed_id": 2},
    ],
)
def test_an_unknown_acting_player_is_rejected(service, delivery, payload):  # AC-15
    err = assert_rejected(service, delivery, payload, ErrorCode.UNKNOWN_PLAYER)
    assert "99" in err.message
