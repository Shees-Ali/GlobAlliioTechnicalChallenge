import pytest

from fakes import new_id
from fastapi.testclient import TestClient

from notifications.api.app import build_default_app, create_app
from notifications.core.notification import Category


@pytest.fixture
def client(service, preference_service) -> TestClient:
    return TestClient(create_app(service, preference_service))


def level_up(player_id: int = 1) -> dict:
    return {"event_id": new_id(), "type": "level_up", "player_id": player_id, "new_level": 15}


def test_a_suppressed_event_returns_200_with_a_suppressed_status(client, delivery, preferences):  # AC-32
    preferences.set(1, Category.GAME, False)

    response = client.post("/events", json=level_up())

    assert (response.status_code, response.json()) == (200, {"status": "suppressed"})
    assert delivery.calls == []


def test_a_valid_change_returns_200_and_is_applied(client, preferences):  # FR-33, FR-35
    response = client.put("/preferences", json={"player_id": 1, "category": "game", "enabled": False})

    assert (response.status_code, response.json()) == (200, {"status": "updated"})
    assert preferences.get(1) == {Category.GAME: False}


@pytest.mark.parametrize(
    ("body", "code"),
    [
        ({"player_id": 99, "category": "game", "enabled": False}, "UNKNOWN_PLAYER"),
        ({"player_id": 1, "category": "pvp", "enabled": False}, "UNSUPPORTED_CATEGORY"),
        ({"player_id": 1, "category": [], "enabled": False}, "UNSUPPORTED_CATEGORY"),  # was a 500
        ({"player_id": 1, "category": {}, "enabled": False}, "UNSUPPORTED_CATEGORY"),  # was a 500
        ({"player_id": 1, "category": "game", "enabled": "false"}, "MALFORMED_FIELD"),
        ({"player_id": 1, "category": "game"}, "MISSING_FIELD"),
    ],
)
def test_a_rejected_change_returns_422_with_its_code(client, preferences, body, code):  # AC-37, FR-35
    response = client.put("/preferences", json=body)

    assert response.status_code == 422
    assert response.json()["code"] == code
    assert response.json()["message"]
    assert preferences.get(1) == {}


@pytest.mark.parametrize("content", ["[1, 2]", "{oops"])
def test_a_body_that_is_not_a_json_object_is_rejected(client, content):
    response = client.put("/preferences", content=content, headers={"content-type": "application/json"})
    assert response.status_code == 422
    assert response.json()["code"] == "MALFORMED_FIELD"


def test_a_change_over_http_applies_to_the_next_posted_event(client, delivery):  # AC-38
    client.put("/preferences", json={"player_id": 1, "category": "game", "enabled": False})

    response = client.post("/events", json=level_up())

    assert response.json() == {"status": "suppressed"}
    assert delivery.calls == []


def test_the_default_app_shares_one_store_between_both_services():  # AC-38
    client = TestClient(build_default_app())

    client.put("/preferences", json={"player_id": 1, "category": "game", "enabled": False})

    assert client.post("/events", json=level_up()).json() == {"status": "suppressed"}
    assert client.post("/events", json=level_up(player_id=2)).json() == {"status": "processed"}
