import pytest

from fakes import new_id

from notifications.core.notification import Category
from notifications.core.service import NotificationService


@pytest.fixture
def service(directory, delivery) -> NotificationService:
    return NotificationService(directory, delivery)


def test_friend_request_from_3_to_1_notifies_user_1_about_user_3(service, delivery):  # AC-4
    service.handle_event({"event_id": new_id(), "type": "friend_request", "requester_id": 3, "recipient_id": 1})

    assert len(delivery.calls) == 1
    notification, token = delivery.calls[0]
    assert notification.recipient_id == 1
    assert notification.category is Category.SOCIAL
    assert notification.event_type == "friend_request"
    assert "Carol" in notification.message  # user 3
    assert "Alice" not in notification.message  # user 1 is the reader, not the subject
    assert token == "token-1"


def test_friend_accepted_by_1_notifies_user_3_about_user_1(service, delivery):  # AC-5
    service.handle_event({"event_id": new_id(), "type": "friend_accepted", "accepter_id": 1, "requester_id": 3})

    assert len(delivery.calls) == 1
    notification, token = delivery.calls[0]
    assert notification.recipient_id == 3
    assert notification.category is Category.SOCIAL
    assert notification.event_type == "friend_accepted"
    assert "Alice" in notification.message  # user 1
    assert "Carol" not in notification.message
    assert token == "token-3"


def test_new_follower_notifies_the_followed_player_about_the_follower(service, delivery):  # AC-6
    service.handle_event({"event_id": new_id(), "type": "new_follower", "follower_id": 4, "followed_id": 2})

    assert len(delivery.calls) == 1
    notification, token = delivery.calls[0]
    assert notification.recipient_id == 2
    assert notification.category is Category.SOCIAL
    assert notification.event_type == "new_follower"
    assert "Dave" in notification.message
    assert "Bob" not in notification.message
    assert token == "token-2"


def test_payloads_carry_ids_and_the_display_name_comes_from_the_directory(service, delivery):  # AC-11
    service.handle_event({"event_id": new_id(), "type": "friend_request", "requester_id": 3, "recipient_id": 1})
    assert "Carol" in delivery.calls[0][0].message


def test_a_social_event_looks_up_the_recipient_and_the_actor(service, directory):  # FR-13
    service.handle_event({"event_id": new_id(), "type": "friend_request", "requester_id": 3, "recipient_id": 1})
    assert sorted(directory.lookups) == [1, 3]
