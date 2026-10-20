"""Simulated game and social producers. They build events in the module's contract and submit them.

They decide nothing about recipients, messages or preferences: that stays in the module.
How an event travels (in-process, HTTP, a broker) is the submit function's concern.
"""

import uuid
from collections.abc import Callable, Mapping
from typing import Any

from notifications.core.service import Outcome

Submit = Callable[[Mapping[str, Any]], Outcome]


class _Producer:
    def __init__(self, submit: Submit) -> None:
        self._submit = submit

    def _send(self, event_type: str, **fields: Any) -> Outcome:
        return self._submit({"event_id": str(uuid.uuid4()), "type": event_type, **fields})


class GameEngine(_Producer):
    def player_leveled_up(self, player_id: int, new_level: int) -> Outcome:
        # brief: gameEngine.playerLeveledUp(1, 15)
        return self._send("level_up", player_id=player_id, new_level=new_level)

    def item_acquired(self, player_id: int, item_name: str) -> Outcome:
        # brief: gameEngine.itemAcquired(2, "SwordOfAzeroth")
        return self._send("item_acquired", player_id=player_id, item_name=item_name)

    def challenge_completed(self, player_id: int, challenge_name: str) -> Outcome:
        # brief style: gameEngine.challengeCompleted(playerId, challengeName)
        return self._send("challenge_completed", player_id=player_id, challenge_name=challenge_name)


class SocialSystem(_Producer):
    def friend_request_sent(self, requester_id: int, recipient_id: int) -> Outcome:
        # brief: socialSystem.friendRequestSent(3, 1)
        return self._send("friend_request", requester_id=requester_id, recipient_id=recipient_id)

    def friend_request_accepted(self, accepter_id: int, requester_id: int) -> Outcome:
        # brief: socialSystem.friendRequestAccepted(1, 3)
        return self._send("friend_accepted", accepter_id=accepter_id, requester_id=requester_id)

    def new_follower(self, follower_id: int, followed_id: int) -> Outcome:
        # brief style: socialSystem.newFollower(followerId, followedId)
        return self._send("new_follower", follower_id=follower_id, followed_id=followed_id)
