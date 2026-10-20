"""AC-61: the README tells a reviewer how to install, run, test and demo, and states the known limits."""

from pathlib import Path

import pytest

README = Path(__file__).resolve().parents[1] / "README.md"


@pytest.mark.parametrize(
    "needed",
    [
        "pip install -e",
        "pytest",
        "uvicorn notifications.api.app:app",
        "python -m notifications.demo",
        "/demo",
        "## Known limitations",
        "gameEngine.playerLeveledUp(1, 15)",  # the brief's call shown next to ours (FR-59, Q25)
        "player_leveled_up(1, 15)",
    ],
)
def test_the_readme_covers_it(needed):  # AC-61, FR-59
    assert needed in README.read_text(encoding="utf-8")
