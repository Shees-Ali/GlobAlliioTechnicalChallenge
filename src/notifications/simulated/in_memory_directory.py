from collections.abc import Iterable

from notifications.core.ports import UserRecord


class InMemoryUserDirectory:
    """Dict-backed stand-in for the user service."""

    def __init__(self, users: Iterable[UserRecord] = ()) -> None:
        self._users = {user.player_id: user for user in users}

    def get(self, player_id: int) -> UserRecord | None:
        return self._users.get(player_id)
