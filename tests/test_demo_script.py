"""The demo script runs the brief's example and the other paths in-process, with no server (AC-54, AC-55)."""

from notifications import demo

EXPECTED_OUTCOMES = [
    "processed",  # gameEngine.playerLeveledUp(1, 15)
    "processed",  # gameEngine.itemAcquired(2, "SwordOfAzeroth")
    "processed",  # socialSystem.friendRequestSent(3, 1)
    "processed",  # socialSystem.friendRequestAccepted(1, 3)
    "processed",  # challenge completed
    "processed",  # new follower
    "suppressed",  # player 4 turned Game off
    "processed",  # player 4 turned Game on again, the next event is delivered
    "undeliverable",  # player 5 has no token
    "DELIVERY_FAILED",  # player 6's channel is unreachable
    "duplicate",  # resend of an earlier event_id
]


def test_the_script_reports_each_step_in_order_without_a_server():  # AC-54
    lines: list[str] = []

    result = demo.run(lines.append)

    assert [step.outcome for step in result.steps] == EXPECTED_OUTCOMES
    assert any("gameEngine.playerLeveledUp(1, 15)" in line for line in lines)
    assert any("Congratulations! You've reached level 15!" in line for line in lines)


def test_each_channel_holds_exactly_what_was_delivered():  # AC-55
    result = demo.run(lambda line: None)

    assert result.feeds == {
        "Alice": ["Congratulations! You've reached level 15!", "Player 'Carol' has sent you a friend request."],
        "Bob": ["You've acquired Sword Of Azeroth!"],
        "Carol": ["Player 'Alice' has accepted your friend request."],
        "Dave": [
            "Challenge completed: Dragon Slayer. Well done!",
            "Player 'Bob' is now following you.",
            "Congratulations! You've reached level 21!",
        ],
        "Eve": [],
        "Frank": [],
    }


def test_the_suppressed_notification_is_not_replayed():  # AC-55, FR-36
    result = demo.run(lambda line: None)

    assert "Congratulations! You've reached level 20!" not in result.feeds["Dave"]


def test_the_listing_is_printed():  # FR-53
    lines: list[str] = []
    demo.run(lines.append)

    assert any("Dave" in line and "level 21" in line for line in lines[-12:])
