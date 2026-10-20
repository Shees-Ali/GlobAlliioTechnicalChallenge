"""Demo adapter: the page, the player list, and a live feed per token over Server-Sent Events. No rules."""

import asyncio
import json
from collections.abc import AsyncIterator, Iterable
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, StreamingResponse

from notifications.core.notification import Category, Notification
from notifications.core.ports import PreferenceStore, UserRecord
from notifications.core.preferences import is_enabled
from notifications.simulated.in_app_channel import InAppChannel, Subscription

PAGE = Path(__file__).parent / "static" / "demo.html"
KEEPALIVE_SECONDS = 15.0


def _sse(event: str, notification: Notification) -> str:
    data = {
        "recipient_id": notification.recipient_id,
        "category": notification.category.value,
        "event_type": notification.event_type,
        "message": notification.message,
        "event_id": notification.event_id,
    }
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def feed_events(subscription: Subscription, keepalive: float = KEEPALIVE_SECONDS) -> AsyncIterator[str]:
    """What the token held when the feed connected, marked history, then each new delivery, marked live."""
    try:
        for notification in subscription.history:
            yield _sse("history", notification)
        while True:
            try:
                notification = await asyncio.wait_for(subscription.next_live(), keepalive)
            except TimeoutError:
                yield ": keep-alive\n\n"
                continue
            if notification is None:  # the feed was closed, the browser reconnects
                return
            yield _sse("live", notification)
    finally:
        subscription.close()  # a disconnect cancels the stream, which releases the feed


def demo_router(
    channel: InAppChannel,
    users: Iterable[UserRecord],
    unreachable_tokens: Iterable[str],
    preferences: PreferenceStore,
) -> APIRouter:
    router = APIRouter()
    unreachable = frozenset(unreachable_tokens)
    users = list(users)

    @router.get("/demo")
    async def page() -> FileResponse:
        return FileResponse(PAGE, media_type="text/html")

    @router.get("/demo/players")
    async def player_list() -> list[dict]:
        # read on every request, so the page's checkboxes match the server after a reload
        return [
            {
                "player_id": user.player_id,
                "display_name": user.display_name,
                "token": user.delivery_token,
                "unreachable": user.delivery_token in unreachable,
                "preferences": {c.value: is_enabled(preferences, user.player_id, c) for c in Category},
            }
            for user in users
        ]

    @router.get("/feeds/{token}")
    async def feed(token: str) -> StreamingResponse:
        # subscribed here, on the server's event loop, which then reads it
        return StreamingResponse(
            feed_events(channel.subscribe(token)),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"},
        )

    return router
