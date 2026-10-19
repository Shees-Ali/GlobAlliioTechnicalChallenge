"""Preference rules: the default-on check and validated changes."""

from collections.abc import Mapping
from typing import Any

from notifications.core.errors import ErrorCode, InvalidPreferenceError
from notifications.core.notification import Category
from notifications.core.ports import PreferenceStore, UserDirectory
from notifications.core.validation import PlayerId

FIELDS = ("player_id", "category", "enabled")


def is_enabled(store: PreferenceStore, player_id: int, category: Category) -> bool:
    """A category with no recorded setting is on (FR-28). This is the only place the default lives."""
    return store.get(player_id).get(category, True)


class PreferenceService:
    """Changes one category setting for one player. Independent of how the change arrived."""

    def __init__(self, directory: UserDirectory, store: PreferenceStore) -> None:
        self._directory = directory
        self._store = store

    def change(self, payload: Any) -> None:
        """Apply {"player_id", "category", "enabled"}, or raise InvalidPreferenceError.

        Every check runs before the store is written, so a rejected change writes nothing.
        """
        if not isinstance(payload, Mapping):
            raise InvalidPreferenceError(ErrorCode.MALFORMED_FIELD, "change must be an object")
        for name in FIELDS:
            if name not in payload:
                raise InvalidPreferenceError(ErrorCode.MISSING_FIELD, f"missing field '{name}'")
        for key in payload:
            if key not in FIELDS:
                raise InvalidPreferenceError(ErrorCode.MALFORMED_FIELD, f"unknown field '{key}'")

        player_id, category, enabled = (payload[name] for name in FIELDS)
        if not PlayerId().accepts(player_id):
            raise InvalidPreferenceError(ErrorCode.MALFORMED_FIELD, "malformed field 'player_id'")
        if category not in {c.value for c in Category}:
            raise InvalidPreferenceError(
                ErrorCode.UNSUPPORTED_CATEGORY, f"unsupported category: {category!r}"
            )
        if not isinstance(enabled, bool):
            raise InvalidPreferenceError(ErrorCode.MALFORMED_FIELD, "malformed field 'enabled'")
        if self._directory.get(player_id) is None:
            raise InvalidPreferenceError(ErrorCode.UNKNOWN_PLAYER, f"unknown player {player_id}")

        self._store.set(player_id, Category(category), enabled)
