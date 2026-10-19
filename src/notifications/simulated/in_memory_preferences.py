import threading

from notifications.core.notification import Category


class InMemoryPreferenceStore:
    """Dict-backed, thread-safe preference store. Lost on restart and not shared between processes."""

    def __init__(self) -> None:
        self._settings: dict[int, dict[Category, bool]] = {}
        self._lock = threading.Lock()

    def get(self, player_id: int) -> dict[Category, bool]:
        with self._lock:
            return dict(self._settings.get(player_id, {}))

    def set(self, player_id: int, category: Category, enabled: bool) -> None:
        with self._lock:
            self._settings.setdefault(player_id, {})[category] = enabled
