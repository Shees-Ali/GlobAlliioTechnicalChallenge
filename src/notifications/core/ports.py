from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from notifications.core.notification import Category, Notification


@dataclass(frozen=True)
class UserRecord:
    player_id: int
    display_name: str
    delivery_token: str | None


@runtime_checkable
class UserDirectory(Protocol):
    """Looks players up by ID. Seam for the real user service."""

    def get(self, player_id: int) -> UserRecord | None: ...


class Claim(Enum):
    """What a claim on an event ID found (FR-61)."""

    NEW = "new"  # the caller now owns the ID, which is in progress
    IN_PROGRESS = "in_progress"  # another copy owns it and has not finished
    COMPLETED = "completed"  # an earlier copy finished: a duplicate


@runtime_checkable
class ProcessedEvents(Protocol):
    """Tracks each event ID through its lifecycle. Seam for a shared store (Redis, a database).

    An ID is claimed (in progress), then either completed or released. Only the caller
    that got Claim.NEW completes or releases it. An ID in progress is never dropped.
    """

    def claim(self, event_id: str) -> Claim:
        """Atomically claim the ID if it is free, and report what was found."""
        ...

    def complete(self, event_id: str) -> None:
        """Mark an ID in progress as completed: later copies are duplicates."""
        ...

    def release(self, event_id: str) -> None:
        """Give back an ID in progress so the event can be processed again. A completed ID stays."""
        ...


@runtime_checkable
class PreferenceStore(Protocol):
    """Holds each player's recorded category settings. Seam for a persistent, shared store.

    It returns only what was recorded. The default for anything missing is a rule in core.
    """

    def get(self, player_id: int) -> Mapping[Category, bool]: ...

    def set(self, player_id: int, category: Category, enabled: bool) -> None: ...


@runtime_checkable
class NotificationDelivery(Protocol):
    """Hands a notification to the in-app channel. Seam for WebSocket delivery.

    The token is never missing or blank: core answers those events as undeliverable.
    Failure is signalled by raising DeliveryError. Returning means the notification was
    handed to the channel, not that the player received or read it.
    """

    def deliver(self, notification: Notification, token: str) -> None: ...
