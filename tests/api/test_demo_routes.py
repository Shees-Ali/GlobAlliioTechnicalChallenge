import asyncio
import json

from fastapi.testclient import TestClient

from fakes import new_id
from notifications.api.app import build_default_app
from notifications.api.demo import feed_events
from notifications.core.notification import Category, Notification
from notifications.simulated.in_app_channel import InAppChannel


def note(n: int) -> Notification:
    return Notification(1, Category.GAME, "level_up", f"message {n}")


def parse(item: str) -> tuple[str, dict]:
    """Split one SSE item into its event name and decoded data."""
    lines = dict(line.split(": ", 1) for line in item.strip().splitlines())
    return lines["event"], json.loads(lines["data"])


async def next_item(stream, timeout: float = 1.0) -> str:
    return await asyncio.wait_for(anext(stream), timeout)


def test_the_stream_sends_held_notifications_as_history_then_new_ones_as_live():  # AC-58, FR-60
    async def scenario():
        channel = InAppChannel()
        channel.deliver(note(1), "token-1")
        channel.deliver(note(2), "token-1")
        stream = feed_events(channel.subscribe("token-1"))

        first, second = await next_item(stream), await next_item(stream)
        channel.deliver(note(3), "token-1")
        third = await next_item(stream)

        assert [parse(i)[0] for i in (first, second, third)] == ["history", "history", "live"]
        assert [parse(i)[1]["message"] for i in (first, second, third)] == ["message 1", "message 2", "message 3"]
        assert parse(third)[1] == {
            "recipient_id": 1,
            "category": "game",
            "event_type": "level_up",
            "message": "message 3",
        }
        await stream.aclose()

    asyncio.run(scenario())


def test_an_idle_stream_sends_a_keep_alive_comment():
    async def scenario():
        stream = feed_events(InAppChannel().subscribe("token-1"), keepalive=0.01)
        assert await next_item(stream) == ": keep-alive\n\n"
        await stream.aclose()

    asyncio.run(scenario())


def test_closing_the_stream_releases_the_feed():  # R11
    async def scenario():
        channel = InAppChannel()
        subscription = channel.subscribe("token-1")
        stream = feed_events(subscription, keepalive=0.01)
        await next_item(stream)

        await stream.aclose()

        assert subscription.closed

    asyncio.run(scenario())


def test_a_closed_feed_ends_its_stream():  # D2: a full feed is closed and the browser reconnects
    async def scenario():
        subscription = InAppChannel().subscribe("token-1")
        stream = feed_events(subscription)
        subscription.close()
        try:
            await next_item(stream)
        except StopAsyncIteration:
            return
        raise AssertionError("the stream should have ended")

    asyncio.run(scenario())


def test_a_posted_event_is_pushed_to_its_tokens_feed_only():  # AC-57, FR-55
    app = build_default_app()
    client = TestClient(app)

    async def scenario():
        mine = feed_events(app.state.channel.subscribe("token-1"), keepalive=0.2)
        other = feed_events(app.state.channel.subscribe("token-2"), keepalive=0.2)

        payload = {"event_id": new_id(), "type": "level_up", "player_id": 1, "new_level": 15}
        assert client.post("/events", json=payload).json() == {"status": "processed"}

        event, data = parse(await next_item(mine))
        assert (event, data["message"]) == ("live", "Congratulations! You've reached level 15!")
        assert await next_item(other) == ": keep-alive\n\n"  # nothing for player 2
        await mine.aclose()
        await other.aclose()

    asyncio.run(scenario())


def test_the_demo_page_is_served():  # AC-56, FR-54
    response = TestClient(build_default_app()).get("/demo")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_the_player_list_gives_each_tokens_and_its_state():  # FR-55, spec edge cases for players 5 and 6
    players = TestClient(build_default_app()).get("/demo/players").json()

    by_id = {p["player_id"]: p for p in players}
    assert sorted(by_id) == [1, 2, 3, 4, 5, 6]
    assert by_id[1] == {
        "player_id": 1,
        "display_name": "Alice",
        "token": "token-1",
        "unreachable": False,
        "preferences": {"game": True, "social": True},  # on until turned off
    }
    assert by_id[5]["token"] is None
    assert by_id[6]["unreachable"] is True


def test_the_player_list_reports_preferences_as_they_are_now():  # so the page's checkboxes match after a reload
    client = TestClient(build_default_app())
    client.put("/preferences", json={"player_id": 4, "category": "game", "enabled": False})

    by_id = {p["player_id"]: p for p in client.get("/demo/players").json()}

    assert by_id[4]["preferences"] == {"game": False, "social": True}
    assert by_id[1]["preferences"] == {"game": True, "social": True}
