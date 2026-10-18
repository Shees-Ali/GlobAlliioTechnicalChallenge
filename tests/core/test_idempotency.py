"""The event ID is the idempotency key (FR-19 to FR-25, decision 11)."""

import pytest

from fakes import new_id
from notifications.core.service import Outcome


def level_up(event_id: str, player_id: int = 1, new_level: int = 15) -> dict:
    return {"event_id": event_id, "type": "level_up", "player_id": player_id, "new_level": new_level}


def test_the_first_submission_is_processed(service, delivery):
    assert service.handle_event(level_up(new_id())) is Outcome.PROCESSED
    assert len(delivery.calls) == 1


def test_the_same_event_submitted_twice_is_delivered_once(service, delivery):  # AC-19
    event = level_up("evt-same")

    service.handle_event(event)
    service.handle_event(event)

    assert len(delivery.calls) == 1


def test_a_duplicate_returns_a_duplicate_outcome_and_not_an_error(service):  # AC-20
    event = level_up("evt-same")

    assert service.handle_event(event) is Outcome.PROCESSED
    assert service.handle_event(event) is Outcome.DUPLICATE


def test_a_duplicate_is_ignored_however_often_it_is_resent(service, delivery):  # AC-19
    for _ in range(5):
        service.handle_event(level_up("evt-same"))
    assert len(delivery.calls) == 1


def test_identical_content_with_different_ids_is_delivered_twice(service, delivery):  # AC-21
    service.handle_event(level_up("evt-1"))  # two real level-ups to the same level
    service.handle_event(level_up("evt-2"))

    assert len(delivery.calls) == 2
    assert delivery.calls[0][0] == delivery.calls[1][0]


@pytest.mark.parametrize(
    "different",
    [
        level_up("evt-same", player_id=2),
        level_up("evt-same", new_level=99),
        {"event_id": "evt-same", "type": "item_acquired", "player_id": 2, "item_name": "Sword"},
    ],
)
def test_the_same_id_with_different_content_is_a_duplicate(service, delivery, different):  # AC-24
    service.handle_event(level_up("evt-same"))

    assert service.handle_event(different) is Outcome.DUPLICATE
    assert len(delivery.calls) == 1
