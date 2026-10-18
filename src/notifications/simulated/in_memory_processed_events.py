import threading
from collections import OrderedDict


class InMemoryProcessedEvents:
    """Bounded, thread-safe set of used event IDs.

    Past `max_entries` the oldest ID is dropped, so a very old ID can be processed again.
    The IDs are lost on restart and not shared between processes.
    """

    def __init__(self, max_entries: int = 10_000) -> None:
        if max_entries < 1:
            raise ValueError("max_entries must be at least 1")
        self._max_entries = max_entries
        self._ids: OrderedDict[str, None] = OrderedDict()
        self._lock = threading.Lock()

    def claim(self, event_id: str) -> bool:
        with self._lock:
            if event_id in self._ids:
                return False
            self._ids[event_id] = None
            if len(self._ids) > self._max_entries:
                self._ids.popitem(last=False)
            return True

    def release(self, event_id: str) -> None:
        with self._lock:
            self._ids.pop(event_id, None)
