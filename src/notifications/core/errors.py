from enum import Enum


class ErrorCode(str, Enum):
    UNSUPPORTED_EVENT_TYPE = "UNSUPPORTED_EVENT_TYPE"
    MISSING_FIELD = "MISSING_FIELD"
    MALFORMED_FIELD = "MALFORMED_FIELD"
    SELF_TARGETED = "SELF_TARGETED"
    UNKNOWN_PLAYER = "UNKNOWN_PLAYER"
    UNSUPPORTED_CATEGORY = "UNSUPPORTED_CATEGORY"
    DELIVERY_FAILED = "DELIVERY_FAILED"
    EVENT_IN_PROGRESS = "EVENT_IN_PROGRESS"


class InvalidEventError(Exception):
    """An event was rejected. Carries a reason code, never a transport detail such as an HTTP status."""

    def __init__(self, code: ErrorCode, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class InvalidPreferenceError(Exception):
    """A preference change was rejected. Same shape as InvalidEventError, so adapters map both alike."""

    def __init__(self, code: ErrorCode, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class DeliveryError(Exception):
    """The in-app channel could not take the notification. A retry may succeed."""

    def __init__(self, message: str):
        super().__init__(message)
        self.code = ErrorCode.DELIVERY_FAILED
        self.message = message


class EventInProgressError(Exception):
    """Another copy of this event is still being processed. Retry later; it may still fail."""

    def __init__(self, event_id: str):
        super().__init__(f"event {event_id} is still being processed, retry later")
        self.code = ErrorCode.EVENT_IN_PROGRESS
        self.message = str(self)
