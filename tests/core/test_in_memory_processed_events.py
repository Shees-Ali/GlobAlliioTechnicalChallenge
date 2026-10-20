import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from notifications.core.ports import Claim, ProcessedEvents
from notifications.simulated.in_memory_processed_events import InMemoryProcessedEvents


def completed(store: InMemoryProcessedEvents, *event_ids: str) -> None:
    for event_id in event_ids:
        assert store.claim(event_id) is Claim.NEW
        store.complete(event_id)


def test_satisfies_the_interface():
    assert isinstance(InMemoryProcessedEvents(), ProcessedEvents)


def test_a_new_id_is_claimed_and_then_in_progress():  # FR-61
    store = InMemoryProcessedEvents()
    assert store.claim("evt-1") is Claim.NEW
    assert store.claim("evt-1") is Claim.IN_PROGRESS


def test_a_completed_id_is_reported_completed():  # FR-61
    store = InMemoryProcessedEvents()
    completed(store, "evt-1")
    assert store.claim("evt-1") is Claim.COMPLETED


def test_different_ids_are_independent():
    store = InMemoryProcessedEvents()
    assert store.claim("evt-1") is Claim.NEW
    assert store.claim("evt-2") is Claim.NEW


def test_release_makes_an_in_progress_id_claimable_again():  # FR-22
    store = InMemoryProcessedEvents()
    store.claim("evt-1")
    store.release("evt-1")
    assert store.claim("evt-1") is Claim.NEW


def test_release_does_not_undo_a_completed_id():  # FR-61: only an in-progress ID is released
    store = InMemoryProcessedEvents()
    completed(store, "evt-1")
    store.release("evt-1")
    assert store.claim("evt-1") is Claim.COMPLETED


def test_releasing_an_unknown_id_does_nothing():
    store = InMemoryProcessedEvents()
    store.release("never-claimed")
    assert store.claim("never-claimed") is Claim.NEW


def test_past_capacity_the_oldest_completed_id_is_dropped():  # AC-26
    store = InMemoryProcessedEvents(max_entries=3)
    completed(store, "a", "b", "c", "d")  # "d" evicts "a"

    assert store.claim("d") is Claim.COMPLETED  # newest ids are still remembered
    assert store.claim("c") is Claim.COMPLETED
    assert store.claim("a") is Claim.NEW  # "a" was dropped, so it is processed again


def test_a_repeat_claim_does_not_refresh_the_age_of_an_id():
    store = InMemoryProcessedEvents(max_entries=2)
    completed(store, "a", "b")
    store.claim("a")  # duplicate, must not make "a" look newer
    completed(store, "c")  # evicts "a", the oldest
    assert store.claim("a") is Claim.NEW


def test_an_id_in_progress_is_never_dropped():  # AC-65, FR-63
    store = InMemoryProcessedEvents(max_entries=2)
    store.claim("running")

    completed(store, "a", "b", "c", "d")

    assert store.claim("running") is Claim.IN_PROGRESS
    assert store.claim("a") is Claim.NEW  # completed ids past the capacity are still dropped
    assert store.claim("d") is Claim.COMPLETED


def test_capacity_must_be_positive():
    with pytest.raises(ValueError):
        InMemoryProcessedEvents(max_entries=0)


def test_concurrent_claims_of_one_id_yield_exactly_one_winner():  # FR-24
    store = InMemoryProcessedEvents()
    workers = 50
    barrier = threading.Barrier(workers)

    def attempt() -> Claim:
        barrier.wait()
        return store.claim("evt-1")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = [f.result() for f in [pool.submit(attempt) for _ in range(workers)]]

    assert results.count(Claim.NEW) == 1
    assert results.count(Claim.IN_PROGRESS) == workers - 1
