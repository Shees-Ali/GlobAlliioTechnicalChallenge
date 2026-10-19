import pytest

from fakes import RecordingDelivery, RecordingDirectory
from notifications.core.ports import UserRecord
from notifications.core.preferences import PreferenceService
from notifications.core.service import NotificationService
from notifications.simulated.in_memory_preferences import InMemoryPreferenceStore
from notifications.simulated.in_memory_processed_events import InMemoryProcessedEvents

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


@pytest.fixture
def processed_events() -> InMemoryProcessedEvents:
    return InMemoryProcessedEvents()


@pytest.fixture
def preferences() -> InMemoryPreferenceStore:
    return InMemoryPreferenceStore()


@pytest.fixture
def service(directory, delivery, processed_events, preferences) -> NotificationService:
    return NotificationService(directory, delivery, processed_events, preferences)


@pytest.fixture
def preference_service(directory, preferences) -> PreferenceService:
    return PreferenceService(directory, preferences)
