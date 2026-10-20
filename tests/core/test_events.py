"""Each event's recipient and content, in one place (FR-1 to FR-13).

Other tests identify a notification by recipient or event_id, not by its text, so a wording
change is made here only.
"""

import pytest

from fakes import new_id
from notifications.core.notification import Category

# Players from conftest: 1 Alice, 2 Bob, 3 Carol, 4 Dave.
EVENTS = [
    # (payload fields, recipient, category, exact message)
    pytest.param(
        {"type": "level_up", "player_id": 1, "new_level": 15},
        1, Category.GAME, "Congratulations! You've reached level 15!",
        id="level_up",  # AC-1
    ),
    pytest.param(
        {"type": "item_acquired", "player_id": 2, "item_name": "SwordOfAzeroth"},
        2, Category.GAME, "You've acquired Sword Of Azeroth!",
        id="item_acquired",  # AC-2, AC-16: a compact name reads as words
    ),
    pytest.param(
        {"type": "challenge_completed", "player_id": 3, "challenge_name": "SlayTheDragon"},
        3, Category.GAME, "Challenge completed: Slay The Dragon. Well done!",
        id="challenge_completed",  # AC-3
    ),
    pytest.param(
        {"type": "friend_request", "requester_id": 3, "recipient_id": 1},
        1, Category.SOCIAL, "Player 'Carol' has sent you a friend request.",
        id="friend_request",  # AC-4: the brief's friendRequestSent(3, 1)
    ),
    pytest.param(
        {"type": "friend_accepted", "accepter_id": 1, "requester_id": 3},
        3, Category.SOCIAL, "Player 'Alice' has accepted your friend request.",
        id="friend_accepted",  # AC-5: the brief's friendRequestAccepted(1, 3) tells the original requester
    ),
    pytest.param(
        {"type": "new_follower", "follower_id": 4, "followed_id": 2},
        2, Category.SOCIAL, "Player 'Dave' is now following you.",
        id="new_follower",  # AC-6
    ),
]


@pytest.mark.parametrize(("fields", "recipient", "category", "message"), EVENTS)
def test_each_event_notifies_the_right_player_with_the_right_content(
    service, delivery, fields, recipient, category, message
):  # AC-1 to AC-7, AC-11, AC-17
    service.handle_event({"event_id": new_id(), **fields})

    [(notification, token)] = delivery.calls
    assert notification.recipient_id == recipient
    assert notification.category is category
    assert notification.event_type == fields["type"]
    assert notification.message == message  # names come from the directory, not the payload (AC-11)
    assert token == f"token-{recipient}"


def test_an_item_name_that_already_has_spaces_is_unchanged(service, delivery):  # AC-16
    service.handle_event({"event_id": new_id(), "type": "item_acquired", "player_id": 2, "item_name": "Sword of Azeroth"})
    assert delivery.calls[0][0].message == "You've acquired Sword of Azeroth!"


@pytest.mark.parametrize("item_name", ["Pebble", "x"])
def test_every_submitted_item_is_notified_with_no_rarity_filter(service, delivery, item_name):  # AC-9
    service.handle_event({"event_id": new_id(), "type": "item_acquired", "player_id": 2, "item_name": item_name})
    assert len(delivery.calls) == 1


def test_a_game_event_looks_up_only_the_recipient(service, directory):  # AC-12
    service.handle_event({"event_id": new_id(), "type": "level_up", "player_id": 1, "new_level": 2})
    assert directory.lookups == [1]


def test_a_social_event_looks_up_the_recipient_and_the_actor(service, directory):  # FR-13
    service.handle_event({"event_id": new_id(), "type": "friend_request", "requester_id": 3, "recipient_id": 1})
    assert sorted(directory.lookups) == [1, 3]
