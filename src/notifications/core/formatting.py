import re

_WORD_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def readable_name(name: str) -> str:
    """Show a compact name such as "SwordOfAzeroth" as separate words.

    A name that already contains whitespace is returned unchanged.
    """
    if any(ch.isspace() for ch in name):
        return name
    return _WORD_BOUNDARY.sub(" ", name)
