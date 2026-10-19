import logging
import threading
from collections import deque
from collections.abc import Iterable

from notifications.core.errors import DeliveryError
from notifications.core.notification import Notification

MAX_NOTIFICATIONS_PER_TOKEN = 100

logger = logging.getLogger("uvicorn.error")


class InAppChannel:
    """Simulated in-app channel. Records what each client would have received, and logs it.

    Keeps the most recent `max_per_token` notifications per token. In memory, lost on restart.
    Tokens in `unreachable_tokens` fail with DeliveryError, to show the failure path.
    """

    def __init__(
        self,
        unreachable_tokens: Iterable[str] = (),
        max_per_token: int = MAX_NOTIFICATIONS_PER_TOKEN,
    ) -> None:
        self._unreachable = frozenset(unreachable_tokens)
        self._max_per_token = max_per_token
        self._delivered: dict[str, deque[Notification]] = {}
        self._lock = threading.Lock()

    def deliver(self, notification: Notification, token: str) -> None:
        if token in self._unreachable:
            raise DeliveryError(f"in-app channel for token {token} is unreachable")
        with self._lock:
            self._delivered.setdefault(token, deque(maxlen=self._max_per_token)).append(notification)
        logger.info(
            "deliver to player %s (token=%s) [%s] %s",
            notification.recipient_id,
            token,
            notification.category.value,
            notification.message,
        )

    def delivered_to(self, token: str) -> list[Notification]:
        with self._lock:
            return list(self._delivered.get(token, ()))
