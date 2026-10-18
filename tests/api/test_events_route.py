import pytest

from fakes import new_id
from fastapi.testclient import TestClient

from notifications.api.app import create_app


@pytest.fixture
def client(service) -> TestClient:
    return TestClient(create_app(service))


def test_a_valid_event_returns_200_and_delivery_has_already_been_invoked(client, delivery):  # AC-8
    response = client.post("/events", json={"event_id": new_id(), "type": "level_up", "player_id": 1, "new_level": 15})

    assert response.status_code == 200
    assert response.json() == {"status": "processed"}
    assert len(delivery.calls) == 1
    assert delivery.calls[0][0].recipient_id == 1


def test_the_brief_example_friend_request_reaches_user_1(client, delivery):
    client.post("/events", json={"event_id": new_id(), "type": "friend_request", "requester_id": 3, "recipient_id": 1})
    notification, _ = delivery.calls[0]
    assert notification.recipient_id == 1
    assert "Carol" in notification.message


@pytest.mark.parametrize(
    ("body", "code"),
    [
        ({"event_id": new_id(), "type": "pvp_defeated", "player_id": 1}, "UNSUPPORTED_EVENT_TYPE"),
        ({"event_id": new_id(), "type": "level_up", "player_id": 1}, "MISSING_FIELD"),
        ({"event_id": new_id(), "type": "level_up", "player_id": 1, "new_level": "15"}, "MALFORMED_FIELD"),
        ({"event_id": new_id(), "type": "level_up", "player_id": 1, "new_level": 5, "x": 1}, "MALFORMED_FIELD"),
        ({"event_id": new_id(), "type": "new_follower", "follower_id": 3, "followed_id": 3}, "SELF_TARGETED"),
        ({"event_id": new_id(), "type": "level_up", "player_id": 99, "new_level": 5}, "UNKNOWN_PLAYER"),
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


def test_a_duplicate_event_returns_200_with_a_duplicate_status(client, delivery):  # AC-20, AC-19
    body = {"event_id": "evt-http-dup", "type": "level_up", "player_id": 1, "new_level": 15}

    first = client.post("/events", json=body)
    second = client.post("/events", json=body)

    assert (first.status_code, first.json()) == (200, {"status": "processed"})
    assert (second.status_code, second.json()) == (200, {"status": "duplicate"})
    assert len(delivery.calls) == 1


def test_the_same_content_with_a_new_event_id_is_delivered_again(client, delivery):  # AC-21
    client.post("/events", json={"event_id": new_id(), "type": "level_up", "player_id": 1, "new_level": 15})
    second = client.post("/events", json={"event_id": new_id(), "type": "level_up", "player_id": 1, "new_level": 15})

    assert second.json() == {"status": "processed"}
    assert len(delivery.calls) == 2


def test_an_event_without_an_event_id_returns_422(client, delivery):  # AC-18
    response = client.post("/events", json={"type": "level_up", "player_id": 1, "new_level": 15})

    assert response.status_code == 422
    assert response.json()["code"] == "MISSING_FIELD"
    assert "event_id" in response.json()["message"]
    assert delivery.calls == []


def test_a_rejected_event_can_be_resent_corrected_with_the_same_id(client, delivery):  # AC-22
    bad = {"event_id": "evt-fix", "type": "level_up", "player_id": 99, "new_level": 5}
    good = {"event_id": "evt-fix", "type": "level_up", "player_id": 1, "new_level": 5}

    assert client.post("/events", json=bad).status_code == 422
    resent = client.post("/events", json=good)

    assert resent.json() == {"status": "processed"}
    assert len(delivery.calls) == 1
