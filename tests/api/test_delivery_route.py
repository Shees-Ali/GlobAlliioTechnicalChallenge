import pytest

from fakes import RecordingDelivery, RecordingDirectory, new_id
from fastapi.testclient import TestClient

from conftest import USERS
from notifications.api.app import build_default_app, create_app
from notifications.core.errors import DeliveryError
from notifications.core.ports import UserRecord
from notifications.core.preferences import PreferenceService
from notifications.core.service import NotificationService


class Raising(RecordingDelivery):
    def __init__(self, error: Exception) -> None:
        super().__init__()
        self.error = error

    def deliver(self, notification, token):
        raise self.error


def client_with(delivery, processed_events, preferences) -> TestClient:
    directory = RecordingDirectory([*USERS, UserRecord(7, "Grace", None)])
    service = NotificationService(directory, delivery, processed_events, preferences)
    # raise_server_exceptions=False so an unexpected error is seen as the 500 a producer would get
    return TestClient(create_app(service, PreferenceService(directory, preferences)), raise_server_exceptions=False)


def level_up(player_id: int) -> dict:
    return {"event_id": new_id(), "type": "level_up", "player_id": player_id, "new_level": 15}


def test_a_delivery_failure_returns_503_with_delivery_failed(processed_events, preferences):  # AC-45
    client = client_with(Raising(DeliveryError("channel is down")), processed_events, preferences)

    response = client.post("/events", json=level_up(1))

    assert response.status_code == 503
    assert response.json() == {"code": "DELIVERY_FAILED", "message": "channel is down"}


def test_an_undeliverable_event_returns_200_with_undeliverable(processed_events, preferences):  # AC-46
    delivery = RecordingDelivery()
    client = client_with(delivery, processed_events, preferences)

    response = client.post("/events", json=level_up(7))

    assert (response.status_code, response.json()) == (200, {"status": "undeliverable"})
    assert delivery.calls == []


def test_any_other_delivery_exception_is_not_reported_as_503(processed_events, preferences):
    client = client_with(Raising(RuntimeError("a bug")), processed_events, preferences)

    assert client.post("/events", json=level_up(1)).status_code == 500


def test_the_default_app_delivers_to_the_simulated_channel():  # AC-47
    app = build_default_app()
    client = TestClient(app)

    assert client.post("/events", json=level_up(1)).json() == {"status": "processed"}

    [held] = app.state.channel.delivered_to("token-1")
    assert held.recipient_id == 1


def test_the_default_app_has_a_player_with_no_token():  # AC-47, AC-46
    client = TestClient(build_default_app())
    assert client.post("/events", json=level_up(5)).json() == {"status": "undeliverable"}


def test_the_default_app_has_a_player_whose_channel_is_unreachable():  # AC-47, AC-51
    client = TestClient(build_default_app())

    response = client.post("/events", json=level_up(6))

    assert response.status_code == 503
    assert response.json()["code"] == "DELIVERY_FAILED"
