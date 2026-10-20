"""The event-ID lifecycle: in progress, completed, released (FR-61 to FR-63, decision 34).

The two sequences below are the ones an external review reproduced against the old two-state store.
"""

import threading

import pytest

from fakes import RecordingDelivery, new_id
from notifications.core.errors import DeliveryError, ErrorCode, EventInProgressError
from notifications.core.service import NotificationService, Outcome
from notifications.simulated.in_memory_processed_events import InMemoryProcessedEvents


def level_up(event_id: str) -> dict:
    return {"event_id": event_id, "type": "level_up", "player_id": 1, "new_level": 15}


class Gate(RecordingDelivery):
    """Holds the first delivery until released, so a test can act while it is in progress."""

    def __init__(self, fail_first: bool = False) -> None:
        super().__init__()
        self.entered, self.go = threading.Event(), threading.Event()
        self.fail_first = fail_first
        self._first = True

    def deliver(self, notification, token):
        if self._first:
            self._first = False
            self.entered.set()
            self.go.wait(timeout=5)
            if self.fail_first:
                raise DeliveryError("channel is down")
        super().deliver(notification, token)


def run_in_background(target) -> tuple[threading.Thread, dict]:
    result: dict = {}

    def runner():
        try:
            result["outcome"] = target()
        except Exception as error:  # noqa: BLE001 - recorded for the assertion
            result["error"] = error

    thread = threading.Thread(target=runner)
    thread.start()
    return thread, result


def test_a_copy_sent_while_the_original_is_in_progress_is_rejected_as_retryable(directory, preferences):  # AC-63
    gate = Gate(fail_first=True)
    service = NotificationService(directory, gate, InMemoryProcessedEvents(), preferences)
    event = level_up(new_id())

    thread, first = run_in_background(lambda: service.handle_event(event))
    assert gate.entered.wait(timeout=5)

    with pytest.raises(EventInProgressError) as copy:
        service.handle_event(event)
    assert copy.value.code is ErrorCode.EVENT_IN_PROGRESS

    gate.go.set()
    thread.join()
    assert isinstance(first["error"], DeliveryError)  # the original failed after all
    assert gate.calls == []  # nothing was delivered, and the copy was not told otherwise

    assert service.handle_event(event) is Outcome.PROCESSED  # the resend now goes through
    assert len(gate.calls) == 1


def test_an_id_in_progress_is_not_evicted_so_it_never_runs_twice(directory, preferences):  # AC-65, FR-63
    gate = Gate()
    service = NotificationService(directory, gate, InMemoryProcessedEvents(max_entries=1), preferences)
    event = level_up(new_id())

    thread, _ = run_in_background(lambda: service.handle_event(event))
    assert gate.entered.wait(timeout=5)

    service.handle_event(level_up(new_id()))  # fills the store; must not push out the running ID
    with pytest.raises(EventInProgressError):
        service.handle_event(event)

    gate.go.set()
    thread.join()
    assert len(gate.calls) == 2  # the other event and the original, once each
    assert service.handle_event(event) is Outcome.DUPLICATE


def test_a_copy_sent_after_completion_is_a_duplicate(service, delivery):  # AC-66, FR-61
    event = level_up(new_id())
    assert service.handle_event(event) is Outcome.PROCESSED
    assert service.handle_event(event) is Outcome.DUPLICATE
    assert len(delivery.calls) == 1
