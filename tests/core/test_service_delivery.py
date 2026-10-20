"""The delivery contract inside handle_event (feature 003)."""

import pytest

from conftest import USERS
from fakes import RecordingDelivery, RecordingDirectory, new_id

from notifications.core.errors import DeliveryError, ErrorCode
from notifications.core.notification import Category
from notifications.core.ports import UserRecord
from notifications.core.service import NotificationService, Outcome
from notifications.simulated.in_app_channel import InAppChannel

NO_TOKEN, EMPTY_TOKEN, BLANK_TOKEN = 7, 8, 9


@pytest.fixture
def directory() -> RecordingDirectory:
    return RecordingDirectory(
        [
            *USERS,
            UserRecord(NO_TOKEN, "Grace", None),
            UserRecord(EMPTY_TOKEN, "Heidi", ""),
            UserRecord(BLANK_TOKEN, "Ivan", "   "),
        ]
    )


def level_up(player_id: int, event_id: str | None = None) -> dict:
    return {"event_id": event_id or new_id(), "type": "level_up", "player_id": player_id, "new_level": 15}


def test_a_recipient_with_no_token_is_undeliverable(service, delivery):  # AC-41
    assert service.handle_event(level_up(NO_TOKEN)) is Outcome.UNDELIVERABLE
    assert delivery.calls == []


@pytest.mark.parametrize("player_id", [EMPTY_TOKEN, BLANK_TOKEN])
def test_a_recipient_with_a_blank_token_is_undeliverable(service, delivery, player_id):  # AC-49
    assert service.handle_event(level_up(player_id)) is Outcome.UNDELIVERABLE
    assert delivery.calls == []


def test_a_turned_off_category_is_suppressed_even_with_no_token(service, delivery, preferences):  # AC-43
    preferences.set(NO_TOKEN, Category.GAME, False)

    assert service.handle_event(level_up(NO_TOKEN)) is Outcome.SUPPRESSED
    assert delivery.calls == []


def test_an_undeliverable_event_uses_up_its_id(delivery, processed_events, preferences):  # AC-42
    event = level_up(NO_TOKEN)
    before = NotificationService(
        RecordingDirectory([UserRecord(NO_TOKEN, "Grace", None)]), delivery, processed_events, preferences
    )
    assert before.handle_event(event) is Outcome.UNDELIVERABLE

    # The player has connected since, so the directory now has a token for them.
    after = NotificationService(
        RecordingDirectory([UserRecord(NO_TOKEN, "Grace", "token-7")]), delivery, processed_events, preferences
    )
    assert after.handle_event(event) is Outcome.DUPLICATE
    assert delivery.calls == []


class FailingOnce(RecordingDelivery):
    """Raises DeliveryError on its first call, then works. Counts every attempt."""

    def __init__(self) -> None:
        super().__init__()
        self.attempts = 0

    def deliver(self, notification, token):
        self.attempts += 1
        if self.attempts == 1:
            raise DeliveryError("channel is down")
        super().deliver(notification, token)


def test_a_delivery_failure_reaches_the_caller_and_the_resend_is_delivered(
    directory, processed_events, preferences
):  # AC-44
    delivery = FailingOnce()
    service = NotificationService(directory, delivery, processed_events, preferences)
    event = level_up(1)

    with pytest.raises(DeliveryError) as error:
        service.handle_event(event)
    assert error.value.code is ErrorCode.DELIVERY_FAILED

    assert service.handle_event(event) is Outcome.PROCESSED
    assert len(delivery.calls) == 1


def test_a_failed_delivery_is_attempted_exactly_once(directory, processed_events, preferences):  # AC-48
    delivery = FailingOnce()
    service = NotificationService(directory, delivery, processed_events, preferences)

    with pytest.raises(DeliveryError):
        service.handle_event(level_up(1))
    assert delivery.attempts == 1  # no retry inside the module


def test_a_processed_event_is_held_by_the_channel_under_the_recipients_token(
    directory, processed_events, preferences
):  # AC-39
    channel = InAppChannel()
    service = NotificationService(directory, channel, processed_events, preferences)

    assert service.handle_event(level_up(1)) is Outcome.PROCESSED

    [held] = channel.delivered_to("token-1")
    assert (held.recipient_id, held.category, held.event_type) == (1, Category.GAME, "level_up")
    assert "15" in held.message


def test_a_notification_carries_the_event_id_of_its_event(service, delivery):  # AC-67, FR-64
    service.handle_event({"event_id": "evt-9", "type": "level_up", "player_id": 1, "new_level": 15})

    [(notification, _)] = delivery.calls
    assert notification.event_id == "evt-9"


class TakesEffectThenRaisesOnce(RecordingDelivery):
    """The delivery happens, but the confirmation is lost: the uncertain outcome in FR-64."""

    def __init__(self) -> None:
        super().__init__()
        self.raised = False

    def deliver(self, notification, token):
        super().deliver(notification, token)
        if not self.raised:
            self.raised = True
            raise DeliveryError("acknowledgement lost")


def test_a_repeat_after_an_uncertain_outcome_carries_the_same_event_id(directory, processed_events, preferences):  # AC-67
    delivery = TakesEffectThenRaisesOnce()
    service = NotificationService(directory, delivery, processed_events, preferences)
    event = {"event_id": new_id(), "type": "level_up", "player_id": 1, "new_level": 15}

    with pytest.raises(DeliveryError):
        service.handle_event(event)
    assert service.handle_event(event) is Outcome.PROCESSED

    # Two deliveries took effect (the module does not prevent this), but a receiver can drop the
    # repeat because both carry the same event_id.
    assert [n.event_id for n, _ in delivery.calls] == [event["event_id"]] * 2
