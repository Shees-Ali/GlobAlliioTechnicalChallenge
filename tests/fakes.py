"""Test doubles shared by the suite."""

from notifications.core.notification import Notification
from notifications.core.ports import UserRecord
from notifications.simulated.in_memory_directory import InMemoryUserDirectory


class RecordingDelivery:
    """Stands in for the in-app delivery dependency and remembers every call."""

    def __init__(self) -> None:
        self.calls: list[tuple[Notification, str | None]] = []

    def deliver(self, notification: Notification, token: str | None) -> None:
        self.calls.append((notification, token))


class RecordingDirectory(InMemoryUserDirectory):
    """In-memory directory that records which player IDs were looked up."""

    def __init__(self, users: list[UserRecord]) -> None:
        super().__init__(users)
        self.lookups: list[int] = []

    def get(self, player_id: int) -> UserRecord | None:
        self.lookups.append(player_id)
        return super().get(player_id)
