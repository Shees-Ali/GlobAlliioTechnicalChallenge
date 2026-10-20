import threading
from collections import OrderedDict

from notifications.core.ports import Claim


class InMemoryProcessedEvents:
    """Thread-safe record of event IDs: those in progress, and a bounded record of completed ones.

    An ID in progress is never dropped, so a second copy cannot run while the first is still
    running. Past `max_entries` the oldest completed ID is dropped, so a very old ID can be
    processed again. The IDs are lost on restart and not shared between processes.
    """

    def __init__(self, max_entries: int = 10_000) -> None:
        if max_entries < 1:
            raise ValueError("max_entries must be at least 1")
        self._max_entries = max_entries
        self._in_progress: set[str] = set()
        self._completed: OrderedDict[str, None] = OrderedDict()
        self._lock = threading.Lock()

    def claim(self, event_id: str) -> Claim:
        with self._lock:
            if event_id in self._in_progress:
                return Claim.IN_PROGRESS
            if event_id in self._completed:
                return Claim.COMPLETED
            self._in_progress.add(event_id)
            return Claim.NEW

    def complete(self, event_id: str) -> None:
        with self._lock:
            if event_id not in self._in_progress:
                return  # only the owner of an ID in progress completes it
            self._in_progress.discard(event_id)
            self._completed[event_id] = None
            if len(self._completed) > self._max_entries:
                self._completed.popitem(last=False)

    def release(self, event_id: str) -> None:
        with self._lock:
            self._in_progress.discard(event_id)  # a completed ID stays completed
