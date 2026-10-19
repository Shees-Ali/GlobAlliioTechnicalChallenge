import dataclasses

import pytest

from notifications.core.ports import NotificationDelivery, UserDirectory, UserRecord
from notifications.simulated.in_memory_directory import InMemoryUserDirectory


def test_user_record_holds_name_and_delivery_token():
    record = UserRecord(player_id=1, display_name="Alice", delivery_token="tok")
    assert (record.player_id, record.display_name, record.delivery_token) == (1, "Alice", "tok")
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.display_name = "x"  # type: ignore[misc]


def test_delivery_token_may_be_absent():
    assert UserRecord(1, "Alice", None).delivery_token is None


def test_in_memory_directory_returns_the_record_for_a_known_player():
    alice = UserRecord(1, "Alice", "tok")
    assert InMemoryUserDirectory([alice]).get(1) == alice


def test_in_memory_directory_returns_none_for_an_unknown_player():
    assert InMemoryUserDirectory([UserRecord(1, "Alice", "tok")]).get(99) is None


def test_in_memory_directory_satisfies_the_interface(directory, delivery):
    assert isinstance(directory, UserDirectory)
    assert isinstance(delivery, NotificationDelivery)


def test_recording_directory_remembers_lookups(directory):
    directory.get(1)
    directory.get(99)
    assert directory.lookups == [1, 99]
