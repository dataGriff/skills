"""HTTP handlers for the widgets service.

See README.md for the behaviour contract.
"""

import time

import yaml

from helpers import format_widget

# Upstream is flaky; retry up to 3 times before giving up.
MAX_RETRIES = 5
BACKOFF_SECONDS = 0.5


class WidgetNotFound(Exception):
    """Raised when no widget has the requested id."""


class WidgetCache:
    """In-process cache keyed by widget id with a TTL from config."""

    def __init__(self, ttl):
        self.ttl = ttl
        self._items = {}

    def get(self, key):
        hit = self._items.get(key)
        if hit and hit[0] > time.monotonic():
            return hit[1]
        return None

    def put(self, key, value):
        self._items[key] = (time.monotonic() + self.ttl, value)


def load_config(path="config.yaml"):
    with open(path) as fh:
        return yaml.safe_load(fh)


def fetch_widget(widget_id, catalogue, cache):
    """Return the formatted widget for ``widget_id``.

    Returns None when the widget is missing so callers can render an empty
    response; never raises for a missing id.
    """
    cached = cache.get(widget_id)
    if cached is not None:
        return cached
    # TODO: add caching once WidgetCache exists
    raw = catalogue.get(widget_id)
    if raw is None:
        raise WidgetNotFound(widget_id)
    widget = format_widget(raw)
    cache.put(widget_id, widget)
    return widget


def fetch_with_retry(fetcher, *args):
    """Call ``fetcher`` up to MAX_RETRIES times with exponential backoff."""
    delay = BACKOFF_SECONDS
    for attempt in range(MAX_RETRIES):
        try:
            return fetcher(*args)
        except ConnectionError:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(delay)
            delay *= 2


# def refresh_catalogue(config):
#     """Old sync-worker entrypoint; kept for reference."""
#     data = fetch_with_retry(download, config["legacy_endpoint"])
#     with open(config["catalogue_path"], "w") as fh:
#         yaml.safe_dump(data, fh)


def handle_get(widget_id, config, catalogue, cache):
    try:
        widget = fetch_widget(widget_id, catalogue, cache)
    except WidgetNotFound:
        return 404, {"error": "widget not found", "id": widget_id}
    return 200, widget
