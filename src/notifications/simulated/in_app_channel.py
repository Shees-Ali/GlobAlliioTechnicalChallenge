import asyncio
import logging
import threading
from collections import deque
from collections.abc import Iterable

from notifications.core.errors import DeliveryError
from notifications.core.notification import Notification

MAX_NOTIFICATIONS_PER_TOKEN = 100

logger = logging.getLogger("uvicorn.error")


class Subscription:
    """A live feed for one token: what the token held when it connected, then each new delivery.

    Live items are handed to the feed's event loop, so `deliver` may run on any thread.
    At most `max_live` items may be outstanding (handed off but not yet read). The bound is
    checked before anything is scheduled, and a feed that reaches it is closed rather than
    slowing or failing delivery (FR-66). It reconnects and gets everything as history.
    """

    def __init__(
        self,
        channel: "InAppChannel",
        token: str,
        history: list[Notification],
        max_live: int,
    ) -> None:
        self.token = token
        self.history = history
        self.closed = False
        self._channel = channel
        self._loop = asyncio.get_running_loop()
        self._queue: asyncio.Queue[Notification | None] = asyncio.Queue()  # bounded by _outstanding
        self._max_live = max_live
        self._outstanding = 0
        self._count_lock = threading.Lock()  # deliver runs on any thread, the reader on the loop

    async def next_live(self) -> Notification | None:
        """The next live delivery, or None once the feed is closed."""
        if self.closed and self._queue.empty():
            return None
        return self._taken(await self._queue.get())

    def next_nowait(self) -> Notification | None:
        """The next live delivery already waiting, or None."""
        try:
            return self._taken(self._queue.get_nowait())
        except asyncio.QueueEmpty:
            return None

    def _taken(self, item: Notification | None) -> Notification | None:
        if item is not None:
            with self._count_lock:
                self._outstanding -= 1
        return item

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        self._channel._unsubscribe(self)
        try:
            self._loop.call_soon_threadsafe(self._end)
        except RuntimeError:
            pass  # the feed's loop has already ended, nobody is waiting

    def _offer(self, notification: Notification) -> bool:
        """Hand a delivery to the feed's loop. Never blocks.

        False, with nothing scheduled, if the feed is at its bound or its loop has ended.
        The caller then closes the feed.
        """
        with self._count_lock:
            if self._outstanding >= self._max_live:
                return False  # the reader has stalled: do not schedule any more work for it
            self._outstanding += 1
        try:
            self._loop.call_soon_threadsafe(self._put, notification)
        except RuntimeError:
            return False
        return True

    def _put(self, notification: Notification) -> None:  # runs on the feed's loop
        if not self.closed:
            self._queue.put_nowait(notification)  # cannot be full: _offer bounded it

    def _end(self) -> None:  # runs on the feed's loop: drop what is queued and wake a waiting reader
        while not self._queue.empty():
            self._queue.get_nowait()
        self._queue.put_nowait(None)


class InAppChannel:
    """Simulated in-app channel. Records what each client would have received, and logs it.

    Keeps the most recent `max_per_token` notifications per token. In memory, lost on restart.
    Tokens in `unreachable_tokens` fail with DeliveryError, to show the failure path.
    Open feeds (`subscribe`) receive each delivery to their token as it happens.
    """

    def __init__(
        self,
        unreachable_tokens: Iterable[str] = (),
        max_per_token: int = MAX_NOTIFICATIONS_PER_TOKEN,
    ) -> None:
        self._unreachable = frozenset(unreachable_tokens)
        self._max_per_token = max_per_token
        self._delivered: dict[str, deque[Notification]] = {}
        self._subscriptions: dict[str, list[Subscription]] = {}
        self._lock = threading.Lock()

    def deliver(self, notification: Notification, token: str) -> None:
        if token in self._unreachable:
            raise DeliveryError(f"in-app channel for token {token} is unreachable")
        with self._lock:
            self._delivered.setdefault(token, deque(maxlen=self._max_per_token)).append(notification)
            ended = [s for s in self._subscriptions.get(token, ()) if not s._offer(notification)]
        for subscription in ended:  # outside the lock, because closing unsubscribes
            subscription.close()
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

    def subscribe(self, token: str, max_live: int = MAX_NOTIFICATIONS_PER_TOKEN) -> Subscription:
        """Open a feed for a token. Call from the event loop that will read it.

        The history snapshot and the registration share the delivery lock, so each
        delivery is either in the history or offered live, never both and never neither.
        """
        with self._lock:
            subscription = Subscription(self, token, list(self._delivered.get(token, ())), max_live)
            self._subscriptions.setdefault(token, []).append(subscription)
        return subscription

    def _unsubscribe(self, subscription: Subscription) -> None:
        with self._lock:
            feeds = self._subscriptions.get(subscription.token, [])
            if subscription in feeds:
                feeds.remove(subscription)
