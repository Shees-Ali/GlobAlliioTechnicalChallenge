"""The registry of supported event types.

Adding an event type means adding one EventDefinition here. Nothing else changes.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from notifications.core.notification import Category
from notifications.core.validation import FieldSpec, PlayerId, PositiveInt

# (event fields, acting player's display name or None) -> message
MessageBuilder = Callable[[Mapping[str, Any], str | None], str]


@dataclass(frozen=True)
class EventDefinition:
    type: str
    category: Category
    fields: tuple[FieldSpec, ...]
    recipient_field: str
    build_message: MessageBuilder
    actor_field: str | None = None  # set when the message names another player


LEVEL_UP = EventDefinition(
    type="level_up",
    category=Category.GAME,
    fields=(FieldSpec("player_id", PlayerId()), FieldSpec("new_level", PositiveInt())),
    recipient_field="player_id",
    build_message=lambda f, _actor: f"Congratulations! You've reached level {f['new_level']}!",
)

REGISTRY: dict[str, EventDefinition] = {d.type: d for d in (LEVEL_UP,)}
