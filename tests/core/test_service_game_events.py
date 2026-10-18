import pytest

from fakes import new_id

from notifications.core.notification import Category


def test_item_acquired_notifies_the_player_with_a_readable_item_name(service, delivery):  # AC-2, AC-16
    service.handle_event({"event_id": new_id(), "type": "item_acquired", "player_id": 2, "item_name": "SwordOfAzeroth"})

    notification, token = delivery.calls[0]
    assert len(delivery.calls) == 1
    assert notification.recipient_id == 2
    assert notification.category is Category.GAME
    assert notification.event_type == "item_acquired"
    assert "Sword Of Azeroth" in notification.message
    assert token == "token-2"


def test_an_item_name_with_spaces_appears_unchanged(service, delivery):  # AC-16
    service.handle_event({"event_id": new_id(), "type": "item_acquired", "player_id": 2, "item_name": "Sword of Azeroth"})
    assert "Sword of Azeroth" in delivery.calls[0][0].message


def test_challenge_completed_notifies_the_player_with_the_quest_name(service, delivery):  # AC-3
    service.handle_event(
        {"event_id": new_id(), "type": "challenge_completed", "player_id": 3, "challenge_name": "SlayTheDragon"}
    )

    notification, _ = delivery.calls[0]
    assert len(delivery.calls) == 1
    assert notification.recipient_id == 3
    assert notification.category is Category.GAME
    assert notification.event_type == "challenge_completed"
    assert "Slay The Dragon" in notification.message


@pytest.mark.parametrize("name", ["Pebble", "x", "A Very Ordinary Stick", "Item-42", "SwordOfAzeroth"])
def test_every_submitted_item_is_notified_with_no_rarity_filter(service, delivery, name):  # AC-9
    service.handle_event({"event_id": new_id(), "type": "item_acquired", "player_id": 2, "item_name": name})
    assert len(delivery.calls) == 1


@pytest.mark.parametrize("name", ["Easy Quest", "y", "FinalBoss"])
def test_every_submitted_challenge_is_notified(service, delivery, name):  # AC-9
    service.handle_event({"event_id": new_id(), "type": "challenge_completed", "player_id": 3, "challenge_name": name})
    assert len(delivery.calls) == 1


def test_game_events_look_up_only_the_recipient(service, directory):  # AC-12
    service.handle_event({"event_id": new_id(), "type": "item_acquired", "player_id": 2, "item_name": "Pebble"})
    service.handle_event({"event_id": new_id(), "type": "challenge_completed", "player_id": 3, "challenge_name": "Quest"})
    assert directory.lookups == [2, 3]
