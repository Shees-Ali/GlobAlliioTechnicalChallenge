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
class NotificationDelivery(Protocol):
    """Hands a notification to the in-app channel. Seam for WebSocket delivery.

    The contract beyond this signature (failures, missing token) is feature 003.
    """

    def deliver(self, notification: Notification, token: str | None) -> None: ...
