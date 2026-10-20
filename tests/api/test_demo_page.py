"""AC-60, automated half: the page offers every action and talks to the right routes.

The interaction itself is checked by hand in a browser (Q27) and recorded in the decision log.
"""

import pytest

from notifications.api.demo import PAGE
from notifications.core.events import REGISTRY

HTML = PAGE.read_text(encoding="utf-8")


@pytest.mark.parametrize("event_type", sorted(REGISTRY))
def test_the_page_can_fire_every_event_type(event_type):  # FR-57
    assert f'"{event_type}"' in HTML


@pytest.mark.parametrize("route", ["/events", "/preferences", "/feeds/", "/demo/players"])
def test_the_page_uses_the_existing_routes(route):  # FR-57, FR-55
    assert route in HTML


def test_the_page_has_preference_controls_and_a_resend():  # FR-57
    assert '"game"' in HTML and '"social"' in HTML
    assert 'id="resend"' in HTML


def test_the_page_tells_history_from_live():  # FR-60
    assert 'addEventListener("history"' in HTML
    assert 'addEventListener("live"' in HTML
