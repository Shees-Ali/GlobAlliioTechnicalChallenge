import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from notifications.core.ports import ProcessedEvents
from notifications.simulated.in_memory_processed_events import InMemoryProcessedEvents


def test_satisfies_the_interface():
    assert isinstance(InMemoryProcessedEvents(), ProcessedEvents)


def test_the_first_claim_succeeds_and_a_repeat_does_not():
    store = InMemoryProcessedEvents()
    assert store.claim("evt-1") is True
    assert store.claim("evt-1") is False


def test_different_ids_are_independent():
    store = InMemoryProcessedEvents()
    assert store.claim("evt-1") is True
    assert store.claim("evt-2") is True


def test_release_makes_the_id_claimable_again():
    store = InMemoryProcessedEvents()
    store.claim("evt-1")
    store.release("evt-1")
    assert store.claim("evt-1") is True


def test_releasing_an_unknown_id_does_nothing():
    store = InMemoryProcessedEvents()
    store.release("never-claimed")
    assert store.claim("never-claimed") is True


def test_past_capacity_the_oldest_id_is_dropped():  # AC-26
    store = InMemoryProcessedEvents(max_entries=3)
    for event_id in ["a", "b", "c"]:
        assert store.claim(event_id) is True

    assert store.claim("d") is True  # evicts "a"
    assert store.claim("d") is False  # newest ids are still remembered
    assert store.claim("c") is False
    assert store.claim("a") is True  # "a" was dropped, so it is processed again


def test_a_repeat_claim_does_not_refresh_the_age_of_an_id():
    store = InMemoryProcessedEvents(max_entries=2)
    store.claim("a")
    store.claim("b")
    store.claim("a")  # duplicate, must not make "a" look newer
    store.claim("c")  # evicts "a", the oldest
    assert store.claim("a") is True


def test_capacity_must_be_positive():
    with pytest.raises(ValueError):
        InMemoryProcessedEvents(max_entries=0)


def test_concurrent_claims_of_one_id_yield_exactly_one_winner():  # FR-24
    store = InMemoryProcessedEvents()
    workers = 50
    barrier = threading.Barrier(workers)

    def attempt() -> bool:
        barrier.wait()
        return store.claim("evt-1")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = [f.result() for f in [pool.submit(attempt) for _ in range(workers)]]

    assert results.count(True) == 1
