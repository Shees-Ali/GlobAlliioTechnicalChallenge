import pytest

from notifications.core.events import REGISTRY
from notifications.core.service import Outcome
from notifications.core.validation import validate_payload
from notifications.simulated.producers import GameEngine, SocialSystem

SPECS = {name: d.fields for name, d in REGISTRY.items()}


class RecordingSubmit:
    def __init__(self, outcome: Outcome = Outcome.PROCESSED) -> None:
        self.payloads: list[dict] = []
        self.outcome = outcome

    def __call__(self, payload):
        self.payloads.append(dict(payload))
        return self.outcome


def test_level_up_submits_one_valid_event_and_returns_the_outcome():  # AC-52
    submit = RecordingSubmit(Outcome.SUPPRESSED)

    outcome = GameEngine(submit).player_leveled_up(1, 15)

    assert outcome is Outcome.SUPPRESSED
    [payload] = submit.payloads
    event = validate_payload(payload, SPECS)
    assert event.event_type == "level_up"
    assert event.fields == {"player_id": 1, "new_level": 15}


def test_each_call_gets_a_new_event_id():  # AC-52
    submit = RecordingSubmit()
    engine = GameEngine(submit)

    engine.player_leveled_up(1, 15)
    engine.player_leveled_up(1, 15)

    first, second = (p["event_id"] for p in submit.payloads)
    assert first != second


@pytest.mark.parametrize(
    ("call", "expected"),
    [
        (lambda g, s: g.player_leveled_up(1, 15), {"type": "level_up", "player_id": 1, "new_level": 15}),
        (
            lambda g, s: g.item_acquired(2, "SwordOfAzeroth"),
            {"type": "item_acquired", "player_id": 2, "item_name": "SwordOfAzeroth"},
        ),
        (
            lambda g, s: g.challenge_completed(4, "DragonSlayer"),
            {"type": "challenge_completed", "player_id": 4, "challenge_name": "DragonSlayer"},
        ),
        (
            lambda g, s: s.friend_request_sent(3, 1),
            {"type": "friend_request", "requester_id": 3, "recipient_id": 1},
        ),
        (
            lambda g, s: s.friend_request_accepted(1, 3),
            {"type": "friend_accepted", "accepter_id": 1, "requester_id": 3},
        ),
        (
            lambda g, s: s.new_follower(2, 4),
            {"type": "new_follower", "follower_id": 2, "followed_id": 4},
        ),
    ],
)
def test_each_call_builds_its_event_in_the_briefs_argument_order(call, expected):  # FR-48, FR-49
    submit = RecordingSubmit()

    call(GameEngine(submit), SocialSystem(submit))

    [payload] = submit.payloads
    validate_payload(payload, SPECS)
    assert {k: v for k, v in payload.items() if k != "event_id"} == expected


def test_an_error_from_submit_reaches_the_caller():  # FR-49
    def failing(payload):
        raise RuntimeError("transport down")

    with pytest.raises(RuntimeError, match="transport down"):
        SocialSystem(failing).new_follower(1, 2)
