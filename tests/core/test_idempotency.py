"""The event ID is the idempotency key (FR-19 to FR-25, decision 11)."""

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from fakes import FlakyDelivery, RecordingDelivery, new_id
from notifications.core.errors import InvalidEventError
from notifications.core.service import NotificationService, Outcome


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


# --- claim timing (FR-21, FR-22) -------------------------------------------------


@pytest.mark.parametrize(
    "bad_payload",
    [
        level_up("evt-retry", player_id=99),  # unknown recipient
        {"event_id": "evt-retry", "type": "friend_request", "requester_id": 99, "recipient_id": 1},  # unknown actor
        {"event_id": "evt-retry", "type": "new_follower", "follower_id": 3, "followed_id": 3},  # self-targeted
        {"event_id": "evt-retry", "type": "level_up", "player_id": 1},  # missing field
        {"event_id": "evt-retry", "type": "level_up", "player_id": 1, "new_level": "15"},  # malformed
    ],
)
def test_a_rejected_event_does_not_use_up_its_id(service, delivery, bad_payload):  # AC-22
    with pytest.raises(InvalidEventError):
        service.handle_event(bad_payload)

    corrected = level_up("evt-retry")
    assert service.handle_event(corrected) is Outcome.PROCESSED
    assert len(delivery.calls) == 1


def test_a_failed_delivery_releases_the_id_so_the_resend_is_delivered(directory, processed_events, preferences):  # AC-23
    flaky = FlakyDelivery(fail_times=1)
    service = NotificationService(directory, flaky, processed_events, preferences)
    event = level_up("evt-flaky")

    with pytest.raises(ConnectionError):
        service.handle_event(event)  # the error reaches the submitter
    assert flaky.calls == []

    assert service.handle_event(event) is Outcome.PROCESSED  # the resend works
    assert len(flaky.calls) == 1


def test_once_delivered_after_a_failure_the_id_stays_used(directory, processed_events, preferences):  # AC-23, AC-19
    flaky = FlakyDelivery(fail_times=1)
    service = NotificationService(directory, flaky, processed_events, preferences)
    event = level_up("evt-flaky")

    with pytest.raises(ConnectionError):
        service.handle_event(event)
    service.handle_event(event)

    assert service.handle_event(event) is Outcome.DUPLICATE
    assert len(flaky.calls) == 1


# --- concurrency (FR-24) ----------------------------------------------------------

WORKERS = 50


class SlowDelivery(RecordingDelivery):
    """Widens the window in which a second thread could slip through."""

    def deliver(self, notification, token):
        time.sleep(0.005)
        super().deliver(notification, token)


class RacyProcessedEvents:
    """A deliberately broken store (check, pause, then set). Used only as a control."""

    def __init__(self) -> None:
        self._ids: set[str] = set()

    def claim(self, event_id: str) -> bool:
        if event_id in self._ids:
            return False
        time.sleep(0.002)
        self._ids.add(event_id)
        return True

    def release(self, event_id: str) -> None:
        self._ids.discard(event_id)


def submit_concurrently(service: NotificationService, event: dict) -> list[Outcome]:
    barrier = threading.Barrier(WORKERS)

    def attempt() -> Outcome:
        barrier.wait()
        return service.handle_event(event)

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return [f.result() for f in [pool.submit(attempt) for _ in range(WORKERS)]]


def test_many_threads_submitting_one_event_cause_exactly_one_delivery(directory, processed_events, preferences):  # AC-25
    delivery = SlowDelivery()
    service = NotificationService(directory, delivery, processed_events, preferences)

    outcomes = submit_concurrently(service, level_up("evt-race"))

    assert len(delivery.calls) == 1
    assert outcomes.count(Outcome.PROCESSED) == 1
    assert outcomes.count(Outcome.DUPLICATE) == WORKERS - 1


def test_the_concurrency_test_can_catch_a_double_delivery(directory, preferences):  # control for AC-25
    delivery = SlowDelivery()
    service = NotificationService(directory, delivery, RacyProcessedEvents(), preferences)

    submit_concurrently(service, level_up("evt-race"))

    assert len(delivery.calls) > 1
