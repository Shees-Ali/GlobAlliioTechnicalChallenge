from notifications.core.notification import Category
from notifications.core.ports import PreferenceStore
from notifications.core.preferences import is_enabled
from notifications.simulated.in_memory_preferences import InMemoryPreferenceStore


def test_satisfies_the_interface():
    assert isinstance(InMemoryPreferenceStore(), PreferenceStore)


def test_an_unrecorded_player_has_an_empty_map():
    assert InMemoryPreferenceStore().get(1) == {}


def test_a_setting_is_returned_after_it_is_set():  # FR-26
    store = InMemoryPreferenceStore()
    store.set(1, Category.GAME, False)
    assert store.get(1) == {Category.GAME: False}


def test_setting_one_category_leaves_the_other_unrecorded():  # FR-27
    store = InMemoryPreferenceStore()
    store.set(1, Category.GAME, False)
    assert Category.SOCIAL not in store.get(1)


def test_one_players_settings_do_not_show_up_for_another():  # FR-27
    store = InMemoryPreferenceStore()
    store.set(1, Category.GAME, False)
    assert store.get(2) == {}


def test_the_returned_map_is_a_copy():
    store = InMemoryPreferenceStore()
    store.set(1, Category.GAME, False)
    store.get(1)[Category.GAME] = True
    assert store.get(1) == {Category.GAME: False}


def test_every_category_is_on_when_nothing_is_recorded():  # FR-28
    store = InMemoryPreferenceStore()
    assert all(is_enabled(store, 1, category) for category in Category)


def test_is_enabled_follows_a_recorded_setting():
    store = InMemoryPreferenceStore()
    store.set(1, Category.GAME, False)
    assert is_enabled(store, 1, Category.GAME) is False
    assert is_enabled(store, 1, Category.SOCIAL) is True
    store.set(1, Category.GAME, True)
    assert is_enabled(store, 1, Category.GAME) is True
