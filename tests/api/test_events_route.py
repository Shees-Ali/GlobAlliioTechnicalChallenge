import pytest
from fastapi.testclient import TestClient

from notifications.api.app import create_app
from notifications.core.service import NotificationService


@pytest.fixture
def client(directory, delivery) -> TestClient:
    return TestClient(create_app(NotificationService(directory, delivery)))


def test_a_valid_event_returns_200_and_delivery_has_already_been_invoked(client, delivery):  # AC-8
    response = client.post("/events", json={"type": "level_up", "player_id": 1, "new_level": 15})

    assert response.status_code == 200
    assert response.json() == {"status": "processed"}
    assert len(delivery.calls) == 1
    assert delivery.calls[0][0].recipient_id == 1


def test_the_brief_example_friend_request_reaches_user_1(client, delivery):
    client.post("/events", json={"type": "friend_request", "requester_id": 3, "recipient_id": 1})
    notification, _ = delivery.calls[0]
    assert notification.recipient_id == 1
    assert "Carol" in notification.message


@pytest.mark.parametrize(
    ("body", "code"),
    [
        ({"type": "pvp_defeated", "player_id": 1}, "UNSUPPORTED_EVENT_TYPE"),
        ({"type": "level_up", "player_id": 1}, "MISSING_FIELD"),
        ({"type": "level_up", "player_id": 1, "new_level": "15"}, "MALFORMED_FIELD"),
        ({"type": "level_up", "player_id": 1, "new_level": 5, "x": 1}, "MALFORMED_FIELD"),
        ({"type": "new_follower", "follower_id": 3, "followed_id": 3}, "SELF_TARGETED"),
        ({"type": "level_up", "player_id": 99, "new_level": 5}, "UNKNOWN_PLAYER"),
    ],
)
def test_an_invalid_event_returns_422_with_the_reason_and_no_delivery(client, delivery, body, code):  # AC-13
    response = client.post("/events", json=body)

    assert response.status_code == 422
    assert response.json()["code"] == code
    assert response.json()["message"]
    assert delivery.calls == []


@pytest.mark.parametrize("content", ["[1, 2]", '"text"', "5", "null"])
def test_a_body_that_is_not_a_json_object_is_rejected(client, delivery, content):
    response = client.post("/events", content=content, headers={"content-type": "application/json"})
    assert response.status_code == 422
    assert response.json()["code"] == "MALFORMED_FIELD"
    assert delivery.calls == []


def test_a_body_that_is_not_json_is_rejected(client, delivery):
    response = client.post("/events", content="{oops", headers={"content-type": "application/json"})
    assert response.status_code == 422
    assert response.json()["code"] == "MALFORMED_FIELD"
    assert delivery.calls == []
