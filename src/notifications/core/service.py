from collections.abc import Mapping
from enum import Enum
from typing import Any

from notifications.core.errors import ErrorCode, InvalidEventError
from notifications.core.events import REGISTRY, EventDefinition
from notifications.core.notification import Notification
from notifications.core.ports import (
    NotificationDelivery,
    PreferenceStore,
    ProcessedEvents,
    UserDirectory,
    UserRecord,
)
from notifications.core.preferences import is_enabled
from notifications.core.validation import validate_payload


class Outcome(str, Enum):
    PROCESSED = "processed"
    DUPLICATE = "duplicate"  # same event_id already processed, nothing was delivered
    SUPPRESSED = "suppressed"  # valid, but the recipient has the category off, nothing was delivered


class NotificationService:
    """The entry point. Independent of how an event arrived (HTTP, WebSocket, broker, direct call)."""

    def __init__(
        self,
        directory: UserDirectory,
        delivery: NotificationDelivery,
        processed_events: ProcessedEvents,
        preferences: PreferenceStore,
        registry: Mapping[str, EventDefinition] = REGISTRY,
    ) -> None:
        self._directory = directory
        self._delivery = delivery
        self._processed_events = processed_events
        self._preferences = preferences
        self._registry = registry

    def handle_event(self, payload: Any) -> Outcome:
        """Process one event synchronously.

        Raises InvalidEventError if it is rejected. A repeat of an already processed
        event_id returns Outcome.DUPLICATE and delivers nothing. An event whose category
        the recipient has turned off returns Outcome.SUPPRESSED and delivers nothing.
        """
        specs = {name: d.fields for name, d in self._registry.items()}
        event = validate_payload(payload, specs)
        event_type, fields = event.event_type, event.fields
        definition = self._registry[event_type]

        if (
            definition.actor_field is not None
            and fields[definition.actor_field] == fields[definition.recipient_field]
        ):
            raise InvalidEventError(ErrorCode.SELF_TARGETED, "a player cannot target themselves")

        recipient = self._lookup(fields[definition.recipient_field])
        actor_name = None
        if definition.actor_field is not None:
            actor_name = self._lookup(fields[definition.actor_field]).display_name

        if not self._processed_events.claim(event.event_id):
            return Outcome.DUPLICATE
        try:
            # Checked after the claim, so a suppressed event uses up its ID and is never replayed.
            if not is_enabled(self._preferences, recipient.player_id, definition.category):
                return Outcome.SUPPRESSED
            notification = Notification(
                recipient_id=recipient.player_id,
                category=definition.category,
                event_type=event_type,
                message=definition.build_message(fields, actor_name),
            )
            self._delivery.deliver(notification, recipient.delivery_token)
        except BaseException:
            # Any failure after the claim (preference read or delivery) must not use up the ID,
            # or the producer's retry would be dropped.
            self._processed_events.release(event.event_id)
            raise
        return Outcome.PROCESSED

    def _lookup(self, player_id: int) -> UserRecord:
        record = self._directory.get(player_id)
        if record is None:
            raise InvalidEventError(ErrorCode.UNKNOWN_PLAYER, f"unknown player {player_id}")
        return record
