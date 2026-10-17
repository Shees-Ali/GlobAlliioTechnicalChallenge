import pytest

from fakes import RecordingDelivery, RecordingDirectory
from notifications.core.ports import UserRecord

USERS = [
    UserRecord(1, "Alice", "token-1"),
    UserRecord(2, "Bob", "token-2"),
    UserRecord(3, "Carol", "token-3"),
    UserRecord(4, "Dave", "token-4"),
]


@pytest.fixture
def directory() -> RecordingDirectory:
    return RecordingDirectory(USERS)


@pytest.fixture
def delivery() -> RecordingDelivery:
    return RecordingDelivery()
