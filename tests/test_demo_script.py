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
    assert any("gameEngine.playerLeveledUp(1, 15)" in line for line in lines)  # the brief's call is shown


def test_each_channel_holds_exactly_what_was_delivered():  # AC-55
    result = demo.run(lambda line: None)

    counts = {name: len(messages) for name, messages in result.feeds.items()}
    # Dave: challenge, follower and the level up after re-enabling. The suppressed one is not replayed.
    assert counts == {"Alice": 2, "Bob": 1, "Carol": 1, "Dave": 3, "Eve": 0, "Frank": 0}


def test_the_listing_is_printed():  # FR-53
    lines: list[str] = []
    demo.run(lines.append)

    listing = lines[lines.index("\nWhat each player's in-app channel holds") + 1 :]
    assert [line.split(":")[0].strip() for line in listing] == ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank"]
