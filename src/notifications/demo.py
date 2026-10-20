"""Demo script: the brief's example usage, then every other path, in-process with no server.

Run with `python -m notifications.demo`.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from notifications.core.errors import DeliveryError
from notifications.core.service import Outcome
from notifications.simulated.producers import GameEngine, SocialSystem
from notifications.simulated.wiring import Simulated, build_simulated


@dataclass
class Step:
    call: str
    outcome: str
    delivered: list[str] = field(default_factory=list)


@dataclass
class Result:
    steps: list[Step]
    feeds: dict[str, list[str]]  # display name -> messages held by that player's channel


class _RecordingSubmit:
    """Submits in-process and keeps each payload, so the script can resend one for the duplicate step."""

    def __init__(self, sim: Simulated) -> None:
        self._sim = sim
        self.payloads: list[Mapping[str, Any]] = []

    def __call__(self, payload: Mapping[str, Any]) -> Outcome:
        self.payloads.append(payload)
        return self._sim.service.handle_event(payload)


def run(print_line: Callable[[str], None] = print) -> Result:
    sim = build_simulated()
    submit = _RecordingSubmit(sim)
    game, social = GameEngine(submit), SocialSystem(submit)
    names = {user.player_id: user.display_name for user in sim.users}
    tokens = {user.display_name: user.delivery_token for user in sim.users}
    steps: list[Step] = []

    def held() -> dict[str, list[str]]:
        return {
            name: [n.message for n in sim.channel.delivered_to(token)] if token else []
            for name, token in tokens.items()
        }

    def step(call: str, action: Callable[[], Outcome]) -> None:
        before = held()
        try:
            outcome = action().value
        except DeliveryError as error:
            outcome = error.code.value
        after = held()
        delivered = [f"{name}: {m}" for name in after for m in after[name][len(before[name]) :]]
        steps.append(Step(call, outcome, delivered))
        print_line(f"{len(steps):>2}. {call}")
        print_line(f"    -> {outcome}" + "".join(f"\n       to {d}" for d in delivered))

    def prefer(player_id: int, category: str, enabled: bool) -> None:
        sim.preference_service.change({"player_id": player_id, "category": category, "enabled": enabled})
        print_line(f"    {names[player_id]} turns {category} events {'on' if enabled else 'off'}")

    print_line("The brief's example usage")
    step("game_engine.player_leveled_up(1, 15)   brief: gameEngine.playerLeveledUp(1, 15)", lambda: game.player_leveled_up(1, 15))
    step('game_engine.item_acquired(2, "SwordOfAzeroth")   brief: gameEngine.itemAcquired(2, "SwordOfAzeroth")', lambda: game.item_acquired(2, "SwordOfAzeroth"))
    step("social_system.friend_request_sent(3, 1)   brief: socialSystem.friendRequestSent(3, 1)", lambda: social.friend_request_sent(3, 1))
    step("social_system.friend_request_accepted(1, 3)   brief: socialSystem.friendRequestAccepted(1, 3)", lambda: social.friend_request_accepted(1, 3))

    print_line("\nThe other required events")
    step('game_engine.challenge_completed(4, "DragonSlayer")', lambda: game.challenge_completed(4, "DragonSlayer"))
    step("social_system.new_follower(2, 4)", lambda: social.new_follower(2, 4))

    print_line("\nPreferences: a turned-off category is suppressed and never replayed")
    prefer(4, "game", False)
    step("game_engine.player_leveled_up(4, 20)", lambda: game.player_leveled_up(4, 20))
    prefer(4, "game", True)
    step("game_engine.player_leveled_up(4, 21)", lambda: game.player_leveled_up(4, 21))

    print_line("\nDelivery: no in-app channel, then an unreachable channel")
    step("game_engine.player_leveled_up(5, 3)   (Eve has no token)", lambda: game.player_leveled_up(5, 3))
    step("game_engine.player_leveled_up(6, 7)   (Frank's channel is down)", lambda: game.player_leveled_up(6, 7))

    print_line("\nIdempotency: the producer resends the first event with the same event_id")
    first = submit.payloads[0]
    step(f"resend event_id {first['event_id']}", lambda: sim.service.handle_event(first))

    feeds = held()
    print_line("\nWhat each player's in-app channel holds")
    for name, messages in feeds.items():
        print_line(f"  {name}: " + (" | ".join(messages) if messages else "(nothing)"))
    return Result(steps, feeds)


if __name__ == "__main__":
    run()
