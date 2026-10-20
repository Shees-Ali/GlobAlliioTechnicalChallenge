"""The routes run the synchronous core off the event loop (FR-65, AC-68).

Reproduces the external review's finding: with `async def` routes, a slow delivery blocked the
event loop, so concurrent requests queued behind it and a 10 ms timer fired after ~450 ms.
"""

import asyncio
import time

import httpx2

from conftest import USERS
from fakes import RecordingDelivery, RecordingDirectory, new_id
from notifications.api.app import create_app
from notifications.core.preferences import PreferenceService
from notifications.core.service import NotificationService
from notifications.simulated.in_memory_preferences import InMemoryPreferenceStore
from notifications.simulated.in_memory_processed_events import InMemoryProcessedEvents

DELIVERY_SECONDS = 0.15


class SlowDelivery(RecordingDelivery):
    """Stands in for a blocking network call to a real channel."""

    def deliver(self, notification, token):
        time.sleep(DELIVERY_SECONDS)
        super().deliver(notification, token)


def test_a_slow_delivery_does_not_hold_up_other_requests_or_the_event_loop():  # AC-68
    directory, preferences = RecordingDirectory(USERS), InMemoryPreferenceStore()
    delivery = SlowDelivery()
    service = NotificationService(directory, delivery, InMemoryProcessedEvents(), preferences)
    app = create_app(service, PreferenceService(directory, preferences))

    async def scenario() -> tuple[float, float]:
        transport = httpx2.ASGITransport(app=app)
        async with httpx2.AsyncClient(transport=transport, base_url="http://test") as client:

            async def timer() -> float:
                start = time.perf_counter()
                await asyncio.sleep(0.01)
                return time.perf_counter() - start

            def post():
                event = {"event_id": new_id(), "type": "level_up", "player_id": 1, "new_level": 15}
                return client.post("/events", json=event)

            start = time.perf_counter()
            lag, *responses = await asyncio.gather(timer(), post(), post(), post())
            assert [r.json() for r in responses] == [{"status": "processed"}] * 3
            return lag, time.perf_counter() - start

    timer_lag, total = asyncio.run(scenario())

    assert len(delivery.calls) == 3
    assert timer_lag < 0.1, f"the event loop was blocked for {timer_lag:.3f}s"
    assert total < 3 * DELIVERY_SECONDS, f"the posts ran one after another ({total:.3f}s)"
