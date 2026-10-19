from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from notifications.core.notification import Notification


@dataclass(frozen=True)
class UserRecord:
    player_id: int
    display_name: str
    delivery_token: str | None


@runtime_checkable
class UserDirectory(Protocol):
    """Looks players up by ID. Seam for the real user service."""

    def get(self, player_id: int) -> UserRecord | None: ...


@runtime_checkable
class ProcessedEvents(Protocol):
    """Remembers which event IDs have been used. Seam for a shared store (Redis, a database)."""

    def claim(self, event_id: str) -> bool:
        """Atomically mark the ID as used. True if it was new, False if already used."""
        ...

    def release(self, event_id: str) -> None:
        """Give an ID back so the event can be processed again."""
        ...


@runtime_checkable
class NotificationDelivery(Protocol):
    """Hands a notification to the in-app channel. Seam for WebSocket delivery.

    The contract beyond this signature (failures, missing token) is feature 003.
    """

    def deliver(self, notification: Notification, token: str | None) -> None: ...
