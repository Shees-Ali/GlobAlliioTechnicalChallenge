from notifications.core.service import Outcome
from notifications.simulated.producers import GameEngine, SocialSystem
from notifications.simulated.sample_users import SAMPLE_USERS
from notifications.simulated.wiring import build_simulated


def test_the_service_delivers_to_the_returned_channel():  # FR-51
    sim = build_simulated()

    assert GameEngine(sim.service.handle_event).player_leveled_up(1, 15) is Outcome.PROCESSED

    [held] = sim.channel.delivered_to("token-1")
    assert held.recipient_id == 1
    assert sim.users == list(SAMPLE_USERS)


def test_two_builds_share_no_state():  # spec edge case: the script and the app are separate
    first, second = build_simulated(), build_simulated()

    GameEngine(first.service.handle_event).player_leveled_up(1, 15)
    first.preference_service.change({"player_id": 2, "category": "game", "enabled": False})

    assert second.channel.delivered_to("token-1") == []
    assert GameEngine(second.service.handle_event).player_leveled_up(2, 3) is Outcome.PROCESSED
