import logging

import pytest

from notifications.core.errors import DeliveryError, ErrorCode
from notifications.core.notification import Category, Notification
from notifications.core.ports import NotificationDelivery
from notifications.simulated.in_app_channel import MAX_NOTIFICATIONS_PER_TOKEN, InAppChannel


def note(n: int, recipient: int = 1) -> Notification:
    return Notification(recipient, Category.GAME, "level_up", f"message {n}", f"evt-{n}")


def test_delivery_error_carries_its_code_and_message():
    error = DeliveryError("channel is down")
    assert error.code is ErrorCode.DELIVERY_FAILED
    assert error.message == "channel is down"


def test_satisfies_the_interface():
    assert isinstance(InAppChannel(), NotificationDelivery)


def test_a_token_with_nothing_delivered_reads_back_empty():
    assert InAppChannel().delivered_to("token-1") == []


def test_each_token_holds_only_its_own_notifications_in_order():  # AC-40
    channel = InAppChannel()
    channel.deliver(note(1), "token-1")
    channel.deliver(note(2, recipient=2), "token-2")
    channel.deliver(note(3), "token-1")

    assert channel.delivered_to("token-1") == [note(1), note(3)]
    assert channel.delivered_to("token-2") == [note(2, recipient=2)]


def test_reading_returns_a_copy():
    channel = InAppChannel()
    channel.deliver(note(1), "token-1")
    channel.delivered_to("token-1").clear()
    assert channel.delivered_to("token-1") == [note(1)]


def test_the_default_limit_is_the_named_constant():  # AC-50
    assert MAX_NOTIFICATIONS_PER_TOKEN == 100
    channel = InAppChannel()
    for n in range(MAX_NOTIFICATIONS_PER_TOKEN + 1):
        channel.deliver(note(n), "token-1")
    held = channel.delivered_to("token-1")
    assert len(held) == MAX_NOTIFICATIONS_PER_TOKEN
    assert held[0] == note(1)


def test_past_the_limit_the_oldest_for_that_token_is_dropped():  # AC-50
    channel = InAppChannel(max_per_token=3)
    channel.deliver(note(0, recipient=2), "token-2")
    for n in range(1, 5):
        channel.deliver(note(n), "token-1")

    assert channel.delivered_to("token-1") == [note(2), note(3), note(4)]
    assert channel.delivered_to("token-2") == [note(0, recipient=2)]


def test_an_unreachable_token_raises_and_records_nothing():  # AC-51
    channel = InAppChannel(unreachable_tokens={"token-x"})

    with pytest.raises(DeliveryError):
        channel.deliver(note(1), "token-x")
    assert channel.delivered_to("token-x") == []

    channel.deliver(note(2), "token-1")
    assert channel.delivered_to("token-1") == [note(2)]


def test_each_delivery_is_logged(caplog):  # FR-43
    with caplog.at_level(logging.INFO):
        InAppChannel().deliver(note(7), "token-1")
    assert "token-1" in caplog.text
    assert "message 7" in caplog.text
