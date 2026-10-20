"""Wires the simulated dependencies, so the running app and the demo script use the same ones."""

from dataclasses import dataclass

from notifications.core.ports import UserRecord
from notifications.core.preferences import PreferenceService
from notifications.core.service import NotificationService
from notifications.simulated.in_app_channel import InAppChannel
from notifications.simulated.in_memory_directory import InMemoryUserDirectory
from notifications.simulated.in_memory_preferences import InMemoryPreferenceStore
from notifications.simulated.in_memory_processed_events import InMemoryProcessedEvents
from notifications.simulated.sample_users import SAMPLE_USERS, UNREACHABLE_TOKENS


@dataclass(frozen=True)
class Simulated:
    service: NotificationService
    preference_service: PreferenceService
    channel: InAppChannel
    users: list[UserRecord]


def build_simulated() -> Simulated:
    """Build a fresh set of simulated dependencies. Two calls share no state."""
    directory = InMemoryUserDirectory(SAMPLE_USERS)
    preferences = InMemoryPreferenceStore()  # shared, so a change applies to the next event
    channel = InAppChannel(unreachable_tokens=UNREACHABLE_TOKENS)
    service = NotificationService(directory, channel, InMemoryProcessedEvents(), preferences)
    return Simulated(service, PreferenceService(directory, preferences), channel, list(SAMPLE_USERS))
