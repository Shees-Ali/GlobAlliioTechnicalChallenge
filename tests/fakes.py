"""Test doubles shared by the suite."""

import itertools

from notifications.core.notification import Notification
from notifications.core.ports import UserRecord
from notifications.simulated.in_memory_directory import InMemoryUserDirectory


class RecordingDelivery:
    """Stands in for the in-app delivery dependency and remembers every call."""

    def __init__(self) -> None:
        self.calls: list[tuple[Notification, str]] = []

    def deliver(self, notification: Notification, token: str) -> None:
        self.calls.append((notification, token))


class RecordingDirectory(InMemoryUserDirectory):
    """In-memory directory that records which player IDs were looked up."""

    def __init__(self, users: list[UserRecord]) -> None:
        super().__init__(users)
        self.lookups: list[int] = []

    def get(self, player_id: int) -> UserRecord | None:
        self.lookups.append(player_id)
        return super().get(player_id)


_ids = itertools.count(1)


def new_id() -> str:
    """A fresh event ID, so each test event is a distinct event."""
    return f"evt-{next(_ids)}"


class FlakyDelivery(RecordingDelivery):
    """Delivery that raises for its first `fail_times` calls, then succeeds."""

    def __init__(self, fail_times: int = 1) -> None:
        super().__init__()
        self.remaining_failures = fail_times

    def deliver(self, notification: Notification, token: str) -> None:
        if self.remaining_failures > 0:
            self.remaining_failures -= 1
            raise ConnectionError("delivery channel is down")
        super().deliver(notification, token)
