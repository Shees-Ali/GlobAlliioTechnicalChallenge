import pytest

from notifications.core.service import Outcome
from notifications.simulated.producers import GameEngine, SocialSystem
from notifications.simulated.sample_users import SAMPLE_USERS
from notifications.simulated.wiring import build_simulated


def test_the_service_delivers_to_the_returned_channel():  # FR-51
    sim = build_simulated()

    assert GameEngine(sim.service.handle_event).player_leveled_up(1, 15) is Outcome.PROCESSED

    [held] = sim.channel.delivered_to("token-1")
    assert held.message == "Congratulations! You've reached level 15!"
    assert sim.users == list(SAMPLE_USERS)


def test_two_builds_share_no_state():  # spec edge case: the script and the app are separate
    first, second = build_simulated(), build_simulated()

    GameEngine(first.service.handle_event).player_leveled_up(1, 15)
    first.preference_service.change({"player_id": 2, "category": "game", "enabled": False})

    assert second.channel.delivered_to("token-1") == []
    assert GameEngine(second.service.handle_event).player_leveled_up(2, 3) is Outcome.PROCESSED


@pytest.mark.parametrize(
    ("call", "token", "message"),
    [
        (lambda g, s: g.player_leveled_up(1, 15), "token-1", "Congratulations! You've reached level 15!"),
        (lambda g, s: g.item_acquired(2, "SwordOfAzeroth"), "token-2", "You've acquired Sword Of Azeroth!"),
        (
            lambda g, s: g.challenge_completed(4, "DragonSlayer"),
            "token-4",
            "Challenge completed: Dragon Slayer. Well done!",
        ),
        (lambda g, s: s.friend_request_sent(3, 1), "token-1", "Player 'Carol' has sent you a friend request."),
        (
            lambda g, s: s.friend_request_accepted(1, 3),
            "token-3",
            "Player 'Alice' has accepted your friend request.",
        ),
        (lambda g, s: s.new_follower(2, 4), "token-4", "Player 'Bob' is now following you."),
    ],
)
def test_each_producer_call_reaches_the_right_player_with_the_right_content(call, token, message):  # AC-53
    sim = build_simulated()
    submit = sim.service.handle_event

    assert call(GameEngine(submit), SocialSystem(submit)) is Outcome.PROCESSED

    assert [n.message for n in sim.channel.delivered_to(token)] == [message]
