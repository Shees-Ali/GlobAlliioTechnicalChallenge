from enum import Enum


class ErrorCode(str, Enum):
    UNSUPPORTED_EVENT_TYPE = "UNSUPPORTED_EVENT_TYPE"
    MISSING_FIELD = "MISSING_FIELD"
    MALFORMED_FIELD = "MALFORMED_FIELD"
    SELF_TARGETED = "SELF_TARGETED"
    UNKNOWN_PLAYER = "UNKNOWN_PLAYER"


class InvalidEventError(Exception):
    """An event was rejected. Carries a reason code, never a transport detail such as an HTTP status."""

    def __init__(self, code: ErrorCode, message: str):
        super().__init__(message)
        self.code = code
        self.message = message
