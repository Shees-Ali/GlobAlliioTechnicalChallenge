"""Checks that run over every definition in the registry, so a new event type is covered for free."""

import pytest

from fakes import new_id

from notifications.core.errors import ErrorCode, InvalidEventError
from notifications.core.events import REGISTRY
from notifications.core.notification import Category
from notifications.core.validation import NonEmptyText

VALID_PAYLOADS = {
    "level_up": {"event_id": new_id(), "type": "level_up", "player_id": 1, "new_level": 15},
    "item_acquired": {"event_id": new_id(), "type": "item_acquired", "player_id": 2, "item_name": "SwordOfAzeroth"},
    "challenge_completed": {"event_id": new_id(), "type": "challenge_completed", "player_id": 3, "challenge_name": "Quest"},
    "friend_request": {"event_id": new_id(), "type": "friend_request", "requester_id": 3, "recipient_id": 1},
    "friend_accepted": {"event_id": new_id(), "type": "friend_accepted", "accepter_id": 1, "requester_id": 3},
    "new_follower": {"event_id": new_id(), "type": "new_follower", "follower_id": 4, "followed_id": 2},
}
EXPECTED_CATEGORY = {
    "level_up": Category.GAME,
    "item_acquired": Category.GAME,
    "challenge_completed": Category.GAME,
    "friend_request": Category.SOCIAL,
    "friend_accepted": Category.SOCIAL,
    "new_follower": Category.SOCIAL,
}
ALL_TYPES = sorted(VALID_PAYLOADS)

FIELD_CASES = [
    (event_type, spec.name)
    for event_type, definition in sorted(REGISTRY.items())
    for spec in definition.fields
]


def test_exactly_the_six_required_event_types_are_supported():  # FR-4
    assert sorted(REGISTRY) == ALL_TYPES


@pytest.mark.parametrize("event_type", ALL_TYPES)
def test_each_event_type_belongs_to_the_right_category(service, delivery, event_type):  # FR-5
    service.handle_event(VALID_PAYLOADS[event_type])
    assert delivery.calls[0][0].category is EXPECTED_CATEGORY[event_type]


@pytest.mark.parametrize("event_type", ALL_TYPES)
def test_every_message_is_non_empty_readable_text(service, delivery, event_type):  # AC-7
    service.handle_event(VALID_PAYLOADS[event_type])
    message = delivery.calls[0][0].message
    assert message.strip()
    assert len(message.split()) >= 3


def assert_rejected_without_delivery(service, delivery, payload, code):
    with pytest.raises(InvalidEventError) as info:
        service.handle_event(payload)
    assert info.value.code is code
    assert delivery.calls == []


@pytest.mark.parametrize(("event_type", "field"), FIELD_CASES)
def test_a_missing_field_is_rejected(service, delivery, event_type, field):  # AC-13
    payload = {k: v for k, v in VALID_PAYLOADS[event_type].items() if k != field}
    assert_rejected_without_delivery(service, delivery, payload, ErrorCode.MISSING_FIELD)


@pytest.mark.parametrize(("event_type", "field"), FIELD_CASES)
@pytest.mark.parametrize("bad_value", [None, True, 1.5, [], {}])
def test_a_field_of_the_wrong_type_is_rejected(service, delivery, event_type, field, bad_value):  # AC-13
    payload = {**VALID_PAYLOADS[event_type], field: bad_value}
    assert_rejected_without_delivery(service, delivery, payload, ErrorCode.MALFORMED_FIELD)


@pytest.mark.parametrize(("event_type", "field"), FIELD_CASES)
def test_blank_text_and_non_positive_ids_are_rejected(service, delivery, event_type, field):  # AC-13
    kind = next(s.kind for s in REGISTRY[event_type].fields if s.name == field)
    bad = "   " if isinstance(kind, NonEmptyText) else 0
    payload = {**VALID_PAYLOADS[event_type], field: bad}
    assert_rejected_without_delivery(service, delivery, payload, ErrorCode.MALFORMED_FIELD)


@pytest.mark.parametrize("event_type", ALL_TYPES)
def test_an_unknown_extra_field_is_rejected(service, delivery, event_type):  # AC-13
    payload = {**VALID_PAYLOADS[event_type], "is_admin": True}
    assert_rejected_without_delivery(service, delivery, payload, ErrorCode.MALFORMED_FIELD)


@pytest.mark.parametrize("payload", [{}, {"event_id": new_id(), "type": "pvp_defeated", "player_id": 1}, {"event_id": new_id(), "type": None}])
def test_an_unsupported_event_type_is_rejected(service, delivery, payload):  # AC-13
    assert_rejected_without_delivery(service, delivery, payload, ErrorCode.UNSUPPORTED_EVENT_TYPE)


def test_events_are_independent_of_each_other(service, delivery):  # AC-10
    service.handle_event(VALID_PAYLOADS["level_up"])  # player 1
    service.handle_event(VALID_PAYLOADS["item_acquired"])  # player 2

    (first, first_token), (second, second_token) = delivery.calls
    assert (first.recipient_id, first_token) == (1, "token-1")
    assert (second.recipient_id, second_token) == (2, "token-2")
    assert "15" in first.message and "15" not in second.message
    assert "Sword Of Azeroth" in second.message and "Sword" not in first.message


def test_a_rejected_event_does_not_affect_the_next_one(service, delivery):  # FR-11
    with pytest.raises(InvalidEventError):
        service.handle_event({"event_id": new_id(), "type": "level_up", "player_id": 99, "new_level": 2})
    service.handle_event(VALID_PAYLOADS["level_up"])
    assert len(delivery.calls) == 1
    assert delivery.calls[0][0].recipient_id == 1


@pytest.mark.parametrize("event_type", ALL_TYPES)
def test_a_missing_event_id_is_rejected(service, delivery, event_type):  # AC-18
    payload = {k: v for k, v in VALID_PAYLOADS[event_type].items() if k != "event_id"}
    with pytest.raises(InvalidEventError) as info:
        service.handle_event(payload)
    assert info.value.code is ErrorCode.MISSING_FIELD
    assert "event_id" in info.value.message
    assert delivery.calls == []


@pytest.mark.parametrize("event_type", ALL_TYPES)
@pytest.mark.parametrize("bad_id", [None, True, 5, 1.5, [], {}, "", "   ", "x" * 129])
def test_a_malformed_event_id_is_rejected(service, delivery, event_type, bad_id):  # AC-18
    payload = {**VALID_PAYLOADS[event_type], "event_id": bad_id}
    with pytest.raises(InvalidEventError) as info:
        service.handle_event(payload)
    assert info.value.code is ErrorCode.MALFORMED_FIELD
    assert "event_id" in info.value.message
    assert delivery.calls == []
