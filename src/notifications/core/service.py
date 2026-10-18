from collections.abc import Mapping
from typing import Any

from notifications.core.errors import ErrorCode, InvalidEventError
from notifications.core.events import REGISTRY, EventDefinition
from notifications.core.notification import Notification
from notifications.core.ports import NotificationDelivery, UserDirectory, UserRecord
from notifications.core.validation import validate_payload


class NotificationService:
    """The entry point. Independent of how an event arrived (HTTP, WebSocket, broker, direct call)."""

    def __init__(
        self,
        directory: UserDirectory,
        delivery: NotificationDelivery,
        registry: Mapping[str, EventDefinition] = REGISTRY,
    ) -> None:
        self._directory = directory
        self._delivery = delivery
        self._registry = registry

    def handle_event(self, payload: Any) -> None:
        """Process one event synchronously. Raises InvalidEventError if it is rejected."""
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

        notification = Notification(
            recipient_id=recipient.player_id,
            category=definition.category,
            event_type=event_type,
            message=definition.build_message(fields, actor_name),
        )
        self._delivery.deliver(notification, recipient.delivery_token)

    def _lookup(self, player_id: int) -> UserRecord:
        record = self._directory.get(player_id)
        if record is None:
            raise InvalidEventError(ErrorCode.UNKNOWN_PLAYER, f"unknown player {player_id}")
        return record
