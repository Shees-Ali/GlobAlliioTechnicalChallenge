"""Declarative payload validation. Strict kinds, no coercion, no third-party library."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from notifications.core.errors import ErrorCode, InvalidEventError

TYPE_KEY = "type"
EVENT_ID_KEY = "event_id"


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


class PositiveInt:
    def accepts(self, value: Any) -> bool:
        return _is_int(value) and value > 0


class PlayerId(PositiveInt):
    pass


class NonEmptyText:
    def __init__(self, max_length: int = 200) -> None:
        self.max_length = max_length

    def accepts(self, value: Any) -> bool:
        return isinstance(value, str) and bool(value.strip()) and len(value) <= self.max_length


class EventId(NonEmptyText):
    """The producer's idempotency key: an opaque, non-blank string."""

    def __init__(self) -> None:
        super().__init__(max_length=128)


@dataclass(frozen=True)
class FieldSpec:
    name: str
    kind: PositiveInt | NonEmptyText


@dataclass(frozen=True)
class ValidatedEvent:
    event_type: str
    event_id: str
    fields: dict[str, Any]


def validate_payload(
    payload: Any, specs_by_type: Mapping[str, Sequence[FieldSpec]]
) -> ValidatedEvent:
    """Check a raw payload against the field specs of its event type.

    Every event carries the common fields `type` and `event_id` on top of the fields
    of its type. Returns the validated event, or raises InvalidEventError.
    """
    if not isinstance(payload, Mapping):
        raise InvalidEventError(ErrorCode.MALFORMED_FIELD, "event must be an object")

    event_type = payload.get(TYPE_KEY)
    if not isinstance(event_type, str) or event_type not in specs_by_type:
        raise InvalidEventError(
            ErrorCode.UNSUPPORTED_EVENT_TYPE, f"unsupported event type: {event_type!r}"
        )

    specs = [FieldSpec(EVENT_ID_KEY, EventId()), *specs_by_type[event_type]]
    for spec in specs:
        if spec.name not in payload:
            raise InvalidEventError(ErrorCode.MISSING_FIELD, f"missing field '{spec.name}'")
    for spec in specs:
        if not spec.kind.accepts(payload[spec.name]):
            raise InvalidEventError(ErrorCode.MALFORMED_FIELD, f"malformed field '{spec.name}'")

    allowed = {TYPE_KEY, *(spec.name for spec in specs)}
    for key in payload:
        if key not in allowed:
            raise InvalidEventError(ErrorCode.MALFORMED_FIELD, f"unexpected field '{key}'")

    return ValidatedEvent(
        event_type=event_type,
        event_id=payload[EVENT_ID_KEY],
        fields={spec.name: payload[spec.name] for spec in specs[1:]},
    )
