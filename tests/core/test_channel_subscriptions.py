"""Live feeds on the simulated channel: history on subscribe, then live deliveries (FR-55, FR-56, FR-58)."""

import asyncio
import threading
import time

import pytest

from fakes import new_id
from notifications.core.errors import DeliveryError
from notifications.core.notification import Category, Notification
from notifications.core.ports import UserRecord
from notifications.core.service import NotificationService, Outcome
from notifications.simulated.in_app_channel import InAppChannel
from notifications.simulated.in_memory_directory import InMemoryUserDirectory
from notifications.simulated.in_memory_preferences import InMemoryPreferenceStore
from notifications.simulated.in_memory_processed_events import InMemoryProcessedEvents


def note(n: int, recipient: int = 1) -> Notification:
    return Notification(recipient, Category.GAME, "level_up", f"message {n}", f"evt-{n}")


async def settle() -> None:
    """Let callbacks scheduled with call_soon_threadsafe run."""
    for _ in range(3):
        await asyncio.sleep(0)


async def drain(subscription) -> list[Notification]:
    await settle()
    received = []
    while (item := subscription.next_nowait()) is not None:
        received.append(item)
    return received


def test_a_subscription_gets_what_the_token_holds_as_history_then_live():  # AC-58, FR-56
    async def scenario():
        channel = InAppChannel()
        channel.deliver(note(1), "token-1")
        channel.deliver(note(2), "token-1")

        subscription = channel.subscribe("token-1")
        channel.deliver(note(3), "token-1")

        assert subscription.history == [note(1), note(2)]
        assert await subscription.next_live() == note(3)

    asyncio.run(scenario())


def test_a_token_with_nothing_yet_has_empty_history_and_waits():  # spec edge case
    async def scenario():
        subscription = InAppChannel().subscribe("token-1")
        assert subscription.history == []
        assert await drain(subscription) == []

    asyncio.run(scenario())


def test_a_subscription_receives_only_its_own_tokens_deliveries():  # FR-55
    async def scenario():
        channel = InAppChannel()
        mine, other = channel.subscribe("token-1"), channel.subscribe("token-2")

        channel.deliver(note(1), "token-1")

        assert await drain(mine) == [note(1)]
        assert await drain(other) == []

    asyncio.run(scenario())


def test_two_subscriptions_to_one_token_each_receive_every_delivery():  # spec edge case: page open twice
    async def scenario():
        channel = InAppChannel()
        first, second = channel.subscribe("token-1"), channel.subscribe("token-1")

        channel.deliver(note(1), "token-1")

        assert await drain(first) == [note(1)]
        assert await drain(second) == [note(1)]

    asyncio.run(scenario())


def test_an_unreachable_token_pushes_nothing():  # FR-56: a failed delivery never appears
    async def scenario():
        channel = InAppChannel(unreachable_tokens={"token-x"})
        subscription = channel.subscribe("token-x")

        with pytest.raises(DeliveryError):
            channel.deliver(note(1), "token-x")

        assert await drain(subscription) == []

    asyncio.run(scenario())


def test_a_delivery_while_subscribing_is_history_or_live_never_both_nor_neither():  # FR-60 edge case
    total = 2000

    async def scenario():
        channel = InAppChannel(max_per_token=total)
        started = threading.Event()

        def producer():
            for n in range(total):
                if n == total // 4:
                    started.set()
                channel.deliver(note(n), "token-1")
                time.sleep(0)  # yield, or the thread finishes before the subscribe runs

        thread = threading.Thread(target=producer)
        thread.start()
        started.wait()
        subscription = channel.subscribe("token-1", max_live=total)
        thread.join()

        live = await drain(subscription)
        assert subscription.history and live, "the subscribe must land mid-stream for this test to mean anything"
        assert subscription.history + live == [note(n) for n in range(total)]

    asyncio.run(scenario())


def test_a_feed_that_stops_reading_is_closed_and_delivery_still_succeeds():  # AC-59, FR-58, D2
    async def scenario():
        channel = InAppChannel()
        subscription = channel.subscribe("token-1", max_live=1)

        for n in range(3):
            channel.deliver(note(n), "token-1")  # never raises, never waits
        await settle()

        assert subscription.closed
        assert channel.delivered_to("token-1") == [note(0), note(1), note(2)]
        assert await subscription.next_live() is None  # a closed feed ends its stream

    asyncio.run(scenario())


def test_a_closed_subscription_receives_nothing_and_does_not_break_delivery():  # AC-59, FR-58
    async def scenario():
        channel = InAppChannel()
        subscription = channel.subscribe("token-1")
        subscription.close()

        channel.deliver(note(1), "token-1")

        assert await drain(subscription) == []
        assert channel.delivered_to("token-1") == [note(1)]

    asyncio.run(scenario())


def test_delivery_still_succeeds_after_the_feeds_event_loop_has_ended():  # FR-58
    channel = InAppChannel()

    async def connect():
        return channel.subscribe("token-1")

    subscription = asyncio.run(connect())  # the loop is closed once this returns

    channel.deliver(note(1), "token-1")

    assert subscription.closed
    assert channel.delivered_to("token-1") == [note(1)]


def test_an_undeliverable_event_never_reaches_a_token_issued_later():  # AC-62, FR-56, FR-41
    async def scenario():
        channel = InAppChannel()
        processed, preferences = InMemoryProcessedEvents(), InMemoryPreferenceStore()
        before = InMemoryUserDirectory([UserRecord(1, "Alice", "token-1"), UserRecord(7, "Grace", None)])
        after = InMemoryUserDirectory([UserRecord(1, "Alice", "token-1"), UserRecord(7, "Grace", "token-7")])
        missed = {"event_id": new_id(), "type": "level_up", "player_id": 7, "new_level": 2}

        assert NotificationService(before, channel, processed, preferences).handle_event(missed) is Outcome.UNDELIVERABLE

        service = NotificationService(after, channel, processed, preferences)
        subscription = channel.subscribe("token-7")
        assert subscription.history == []

        assert service.handle_event(missed) is Outcome.DUPLICATE
        assert service.handle_event({**missed, "event_id": new_id(), "new_level": 3}) is Outcome.PROCESSED
        assert [n.message for n in await drain(subscription)] == ["Congratulations! You've reached level 3!"]

    asyncio.run(scenario())


def test_the_feed_bound_is_enforced_before_any_work_is_scheduled():  # AC-69, FR-66
    async def scenario():
        channel = InAppChannel(max_per_token=5000)
        subscription = channel.subscribe("token-1", max_live=1)
        loop = asyncio.get_running_loop()
        scheduled_before = len(loop._ready)  # callbacks waiting to run on this loop

        for n in range(5000):  # the loop never runs during this, as when a reader has stalled
            channel.deliver(note(n), "token-1")

        assert subscription.closed  # closed at the second delivery, not later on the loop
        assert len(loop._ready) - scheduled_before <= 2  # one hand-off and the close, not 5,000
        assert len(channel.delivered_to("token-1")) == 5000  # delivery still recorded everything
        assert await subscription.next_live() is None  # the stream ends; on reconnect it is all history

    asyncio.run(scenario())


def test_reading_frees_room_in_the_feed():  # FR-66: the bound counts items not yet read
    async def scenario():
        channel = InAppChannel()
        subscription = channel.subscribe("token-1", max_live=2)

        for n in range(6):
            channel.deliver(note(n), "token-1")
            assert await subscription.next_live() == note(n)

        assert not subscription.closed

    asyncio.run(scenario())
