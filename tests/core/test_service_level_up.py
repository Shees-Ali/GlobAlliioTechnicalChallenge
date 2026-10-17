import pytest

from notifications.core.notification import Category
from notifications.core.service import NotificationService

LEVEL_UP = {"type": "level_up", "player_id": 1, "new_level": 15}


@pytest.fixture
def service(directory, delivery) -> NotificationService:
    return NotificationService(directory, delivery)


def test_level_up_delivers_one_game_notification_to_the_player(service, delivery):  # AC-1
    service.handle_event(LEVEL_UP)

    assert len(delivery.calls) == 1
    notification, _ = delivery.calls[0]
    assert notification.recipient_id == 1
    assert notification.category is Category.GAME
    assert notification.event_type == "level_up"
    assert "15" in notification.message


def test_delivery_receives_the_recipients_token(service, delivery):  # AC-17
    service.handle_event(LEVEL_UP)
    assert delivery.calls[0][1] == "token-1"


def test_delivery_has_been_invoked_by_the_time_handle_event_returns(service, delivery):  # AC-8
    assert delivery.calls == []
    service.handle_event(LEVEL_UP)
    assert len(delivery.calls) == 1


def test_a_game_event_looks_up_only_the_recipient(service, directory):  # AC-12
    service.handle_event(LEVEL_UP)
    assert directory.lookups == [1]


def test_an_event_with_no_directory_token_is_still_delivered(directory, delivery):  # Q15
    from notifications.core.ports import UserRecord
    from notifications.simulated.in_memory_directory import InMemoryUserDirectory

    service = NotificationService(InMemoryUserDirectory([UserRecord(1, "Alice", None)]), delivery)
    service.handle_event(LEVEL_UP)
    assert delivery.calls[0][1] is None
