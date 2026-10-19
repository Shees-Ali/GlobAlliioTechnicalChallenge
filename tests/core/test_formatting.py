import pytest

from notifications.core.formatting import readable_name


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("SwordOfAzeroth", "Sword Of Azeroth"),  # AC-16
        ("Excalibur", "Excalibur"),
        ("DragonSlayer2", "Dragon Slayer2"),
        ("Sword of Azeroth", "Sword of Azeroth"),  # already has spaces: unchanged
        ("Slay The Dragon", "Slay The Dragon"),
        ("OneAndTwo and three", "OneAndTwo and three"),  # any space means unchanged
    ],
)
def test_readable_name(raw, expected):
    assert readable_name(raw) == expected
