import pytest

from notifications.core.errors import ErrorCode, InvalidEventError
from notifications.core.validation import (
    FieldSpec,
    NonEmptyText,
    PlayerId,
    PositiveInt,
    validate_payload,
)

SPECS = {
    "demo": [
        FieldSpec("player_id", PlayerId()),
        FieldSpec("level", PositiveInt()),
        FieldSpec("label", NonEmptyText(max_length=10)),
    ]
}
VALID = {"type": "demo", "player_id": 1, "level": 15, "label": "hello"}


def rejected(payload) -> InvalidEventError:
    with pytest.raises(InvalidEventError) as info:
        validate_payload(payload, SPECS)
    return info.value


def test_accepts_a_correct_payload_and_returns_type_and_fields():
    assert validate_payload(VALID, SPECS) == (
        "demo",
        {"player_id": 1, "level": 15, "label": "hello"},
    )


@pytest.mark.parametrize("payload", [None, [], "demo", 5, [("type", "demo")]])
def test_rejects_a_payload_that_is_not_an_object(payload):
    assert rejected(payload).code is ErrorCode.MALFORMED_FIELD


@pytest.mark.parametrize("type_value", ["nope", "", 5, None, ["demo"]])
def test_rejects_an_unknown_or_non_string_type(type_value):
    err = rejected({**VALID, "type": type_value})
    assert err.code is ErrorCode.UNSUPPORTED_EVENT_TYPE


def test_rejects_a_missing_type():
    payload = {k: v for k, v in VALID.items() if k != "type"}
    assert rejected(payload).code is ErrorCode.UNSUPPORTED_EVENT_TYPE


@pytest.mark.parametrize("field", ["player_id", "level", "label"])
def test_rejects_a_missing_field_and_names_it(field):
    payload = {k: v for k, v in VALID.items() if k != field}
    err = rejected(payload)
    assert err.code is ErrorCode.MISSING_FIELD
    assert field in err.message


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("player_id", True),  # bool is not an ID
        ("player_id", "1"),
        ("player_id", 1.0),
        ("player_id", 0),
        ("player_id", -3),
        ("player_id", None),
        ("level", "15"),  # no coercion
        ("level", 0),
        ("level", 15.5),
        ("level", False),
        ("label", ""),
        ("label", "   "),
        ("label", 123),
        ("label", None),
        ("label", "x" * 11),  # over max_length
    ],
)
def test_rejects_a_value_of_the_wrong_kind_and_names_the_field(field, bad_value):
    err = rejected({**VALID, field: bad_value})
    assert err.code is ErrorCode.MALFORMED_FIELD
    assert field in err.message


def test_accepts_text_at_the_length_limit():
    assert validate_payload({**VALID, "label": "x" * 10}, SPECS)[1]["label"] == "x" * 10


def test_rejects_an_unknown_extra_field():
    err = rejected({**VALID, "admin": True})
    assert err.code is ErrorCode.MALFORMED_FIELD
    assert "admin" in err.message
