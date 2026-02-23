from datetime import datetime, timedelta
from types import SimpleNamespace

from django.utils import timezone

from stonks_overwatch.constants import BrokerName
from stonks_overwatch.templatetags import custom_tags

import pytest

# ---------------------------------------------------------------------------
# get_connected_tooltip
# ---------------------------------------------------------------------------


def test_get_connected_tooltip_lists_enabled_brokers(monkeypatch: pytest.MonkeyPatch) -> None:
    enabled_brokers = [BrokerName.IBKR, BrokerName.DEGIRO]
    monkeypatch.setattr(custom_tags, "_get_enabled_brokers", lambda factory: enabled_brokers)

    now = timezone.localtime(timezone.now())
    last_updates = {
        BrokerName.DEGIRO: now - timedelta(minutes=4),
        BrokerName.IBKR: now - timedelta(minutes=8),
    }
    monkeypatch.setattr(custom_tags, "_get_last_update_for_broker", lambda broker, factory: last_updates[broker])

    def _fake_config(broker_name: BrokerName, factory):
        return SimpleNamespace(update_frequency_minutes=5)

    monkeypatch.setattr(custom_tags, "_get_broker_config", _fake_config)

    result = custom_tags.get_connected_tooltip()

    assert result == (
        '<div class="broker-status-grid">'
        '<span class="broker-name">DEGIRO:</span><span class="status-emoji">🟢</span><span>Updated 4 minutes ago</span>'
        '<span class="broker-name">IBKR:</span><span class="status-emoji">🟡</span><span>Updated 8 minutes ago</span>'
        "</div>"
    )


def test_get_connected_tooltip_no_update_frequency_shows_red_with_relative_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    enabled_brokers = [BrokerName.IBKR]
    monkeypatch.setattr(custom_tags, "_get_enabled_brokers", lambda factory: enabled_brokers)
    monkeypatch.setattr(
        custom_tags, "_get_last_update_for_broker", lambda broker, factory: timezone.localtime(timezone.now())
    )
    monkeypatch.setattr(custom_tags, "_get_broker_config", lambda broker, factory: None)

    result = custom_tags.get_connected_tooltip()

    assert result == (
        '<div class="broker-status-grid">'
        '<span class="broker-name">IBKR:</span><span class="status-emoji">🔴</span><span>Updated Just now</span>'
        "</div>"
    )


def test_get_connected_tooltip_handles_no_enabled_brokers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(custom_tags, "_get_enabled_brokers", lambda factory: [])

    result = custom_tags.get_connected_tooltip()

    assert result == "No brokers enabled"


# ---------------------------------------------------------------------------
# get_connected_status_level
# ---------------------------------------------------------------------------


def test_get_connected_status_level_is_green_when_all_green(monkeypatch: pytest.MonkeyPatch) -> None:
    enabled_brokers = [BrokerName.DEGIRO, BrokerName.IBKR]
    monkeypatch.setattr(custom_tags, "_get_enabled_brokers", lambda factory: enabled_brokers)
    monkeypatch.setattr(custom_tags, "_get_last_update_for_broker", lambda broker, factory: object())
    monkeypatch.setattr(custom_tags, "_get_update_status_level", lambda broker, _, factory: "ok")

    result = custom_tags.get_connected_status_level()

    assert result == "ok"


def test_get_connected_status_level_is_yellow_when_any_yellow_and_no_red(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    enabled_brokers = [BrokerName.DEGIRO, BrokerName.IBKR]
    monkeypatch.setattr(custom_tags, "_get_enabled_brokers", lambda factory: enabled_brokers)
    monkeypatch.setattr(custom_tags, "_get_last_update_for_broker", lambda broker, factory: object())
    monkeypatch.setattr(
        custom_tags,
        "_get_update_status_level",
        lambda broker, _, factory: "warning" if broker == BrokerName.IBKR else "ok",
    )

    result = custom_tags.get_connected_status_level()

    assert result == "warning"


def test_get_connected_status_level_is_red_when_any_red(monkeypatch: pytest.MonkeyPatch) -> None:
    enabled_brokers = [BrokerName.DEGIRO, BrokerName.IBKR]
    monkeypatch.setattr(custom_tags, "_get_enabled_brokers", lambda factory: enabled_brokers)
    monkeypatch.setattr(custom_tags, "_get_last_update_for_broker", lambda broker, factory: object())
    monkeypatch.setattr(
        custom_tags,
        "_get_update_status_level",
        lambda broker, _, factory: "error" if broker == BrokerName.DEGIRO else "ok",
    )

    result = custom_tags.get_connected_status_level()

    assert result == "error"


# ---------------------------------------------------------------------------
# get_connected_status_icon_class
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "level, expected_class",
    [
        ("ok", "text-success"),
        ("warning", "text-warning"),
        ("error", "text-danger"),
    ],
)
def test_get_connected_status_icon_class(monkeypatch: pytest.MonkeyPatch, level: str, expected_class: str) -> None:
    monkeypatch.setattr(custom_tags, "get_connected_status_level", lambda: level)

    result = custom_tags.get_connected_status_icon_class()

    assert result == expected_class


# ---------------------------------------------------------------------------
# get_connected_status_icon
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "level, expected_icon",
    [
        ("ok", "bi-cloud-check-fill"),
        ("warning", "bi-cloud-fill"),
        ("error", "bi-cloud-slash-fill"),
    ],
)
def test_get_connected_status_icon(monkeypatch: pytest.MonkeyPatch, level: str, expected_icon: str) -> None:
    monkeypatch.setattr(custom_tags, "get_connected_status_level", lambda: level)

    result = custom_tags.get_connected_status_icon()

    assert result == expected_icon


# ---------------------------------------------------------------------------
# _get_last_update_for_broker — fallback behaviour
# ---------------------------------------------------------------------------


def test_get_last_update_for_broker_falls_back_when_service_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeFactory:
        def create_service(self, broker_name: BrokerName, service_type):
            return None

    result = custom_tags._get_last_update_for_broker(BrokerName.IBKR, FakeFactory())

    assert isinstance(result, datetime)
    assert (timezone.now() - result).days >= custom_tags._STALE_FALLBACK_DAYS - 1


def test_get_last_update_for_broker_falls_back_on_service_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeService:
        def get_last_sync(self):
            raise RuntimeError("boom")

    class FakeFactory:
        def create_service(self, broker_name: BrokerName, service_type):
            return FakeService()

    result = custom_tags._get_last_update_for_broker(BrokerName.IBKR, FakeFactory())

    assert isinstance(result, datetime)
    assert (timezone.now() - result).days >= custom_tags._STALE_FALLBACK_DAYS - 1


def test_get_last_update_for_broker_returns_valid_datetime(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = timezone.now() - timedelta(minutes=10)

    class FakeService:
        def get_last_sync(self):
            return expected

    class FakeFactory:
        def create_service(self, broker_name: BrokerName, service_type):
            return FakeService()

    result = custom_tags._get_last_update_for_broker(BrokerName.IBKR, FakeFactory())

    assert result == expected


def test_get_last_update_for_broker_falls_back_when_service_returns_non_datetime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeService:
        def get_last_sync(self):
            return "not a datetime"

    class FakeFactory:
        def create_service(self, broker_name: BrokerName, service_type):
            return FakeService()

    result = custom_tags._get_last_update_for_broker(BrokerName.IBKR, FakeFactory())

    assert (timezone.now() - result).days >= custom_tags._STALE_FALLBACK_DAYS - 1


# ---------------------------------------------------------------------------
# _format_relative_time
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "delta, expected",
    [
        (timedelta(seconds=-5), "Just now"),
        (timedelta(seconds=0), "Just now"),
        (timedelta(seconds=30), "Just now"),
        (timedelta(seconds=59), "Just now"),
        (timedelta(minutes=1), "1 minute ago"),
        (timedelta(minutes=2), "2 minutes ago"),
        (timedelta(minutes=59), "59 minutes ago"),
        (timedelta(hours=1), "1 hour ago"),
        (timedelta(hours=2), "2 hours ago"),
        (timedelta(hours=23), "23 hours ago"),
        (timedelta(hours=24), "Yesterday"),
        (timedelta(hours=35), "Yesterday"),
        (timedelta(hours=36), "1 day ago"),
        (timedelta(days=2), "2 days ago"),
        (timedelta(days=6), "6 days ago"),
        (timedelta(days=7), "1 week ago"),
        (timedelta(days=14), "2 weeks ago"),
        (timedelta(days=29), "4 weeks ago"),
        (timedelta(days=30), "1 month ago"),
        (timedelta(days=60), "2 months ago"),
        (timedelta(days=364), "12 months ago"),
        (timedelta(days=365), "1 year ago"),
        (timedelta(days=730), "2 years ago"),
    ],
)
def test_format_relative_time(delta: timedelta, expected: str) -> None:
    assert custom_tags._format_relative_time(delta) == expected


# ---------------------------------------------------------------------------
# _pluralize
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value, unit, expected",
    [
        (1, "minute", "1 minute ago"),
        (2, "minute", "2 minutes ago"),
        (1, "hour", "1 hour ago"),
        (5, "hour", "5 hours ago"),
        (1, "day", "1 day ago"),
        (1, "week", "1 week ago"),
        (1, "month", "1 month ago"),
        (1, "year", "1 year ago"),
    ],
)
def test_pluralize(value: int, unit: str, expected: str) -> None:
    assert custom_tags._pluralize(value, unit) == expected
