import pytest

from app import MAX_RETRIES, WidgetCache, WidgetNotFound, fetch_widget, fetch_with_retry, handle_get


CATALOGUE = {"w1": {"id": "w1", "name": " Gear ", "price": "1.5", "tags": ["b", "a", "b"]}}


def test_fetch_widget_formats_and_caches():
    cache = WidgetCache(ttl=60)
    widget = fetch_widget("w1", CATALOGUE, cache)
    assert widget == {"id": "w1", "name": "Gear", "price_cents": 150, "tags": ["a", "b"]}
    assert cache.get("w1") == widget


def test_missing_widget_raises():
    with pytest.raises(WidgetNotFound):
        fetch_widget("nope", CATALOGUE, WidgetCache(ttl=60))


def test_handle_get_returns_404_for_missing():
    status, body = handle_get("nope", {}, CATALOGUE, WidgetCache(ttl=60))
    assert status == 404
    assert body["error"] == "widget not found"


def test_retries_five_times(monkeypatch):
    monkeypatch.setattr("app.time.sleep", lambda _: None)
    calls = []

    def flaky():
        calls.append(1)
        raise ConnectionError

    with pytest.raises(ConnectionError):
        fetch_with_retry(flaky)
    assert len(calls) == MAX_RETRIES == 5
