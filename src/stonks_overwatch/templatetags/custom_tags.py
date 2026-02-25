from datetime import datetime, timedelta

from django import template
from django.template import RequestContext
from django.utils import timezone

from stonks_overwatch.constants import BrokerName
from stonks_overwatch.core.factories.broker_factory import BrokerFactory
from stonks_overwatch.core.service_types import ServiceType
from stonks_overwatch.services.aggregators.portfolio_aggregator import PortfolioAggregatorService
from stonks_overwatch.services.models import dataclass_to_dict
from stonks_overwatch.services.utilities.session_manager import SessionManager
from stonks_overwatch.utils.core.logger import StonksLogger

register = template.Library()
LOGGER = StonksLogger.get_logger("stonks_overwatch.views.templates", "[CUSTOM_TAGS]")

# Chosen to guarantee "red" status — far enough in the past to exceed any broker's update window
_STALE_FALLBACK_DAYS = 365


@register.filter
def index(sequence, position):
    return sequence[position]


@register.inclusion_tag("total_overview.html", takes_context=True)
def show_total_portfolio(context: RequestContext) -> dict:
    portfolio = PortfolioAggregatorService()
    selected_portfolio = SessionManager.get_selected_portfolio(context.request)
    total_portfolio = portfolio.get_portfolio_total(selected_portfolio)

    return {"total_portfolio": dataclass_to_dict(total_portfolio)}


def _format_relative_time(delta: timedelta) -> str:
    if delta.total_seconds() < 0:
        return "Just now"

    if delta < timedelta(minutes=1):
        return "Just now"

    if delta < timedelta(hours=1):
        minutes = int(delta.total_seconds() // 60)
        return _pluralize(minutes, "minute")

    if delta < timedelta(days=1):
        hours = int(delta.total_seconds() // 3600)
        return _pluralize(hours, "hour")

    # "Yesterday" covers 24–36 h; beyond that the day count is more accurate
    if delta < timedelta(hours=36):
        return "Yesterday"

    if delta < timedelta(days=7):
        days = int(delta.total_seconds() // 86400)
        return _pluralize(days, "day")

    if delta < timedelta(days=30):
        weeks = int(delta.total_seconds() // 604800)
        return _pluralize(weeks, "week")

    if delta < timedelta(days=365):
        months = int(delta.total_seconds() // 2592000)
        return _pluralize(months, "month")

    years = int(delta.total_seconds() // 31536000)
    return _pluralize(years, "year")


def _pluralize(value: int, unit: str) -> str:
    suffix = "" if value == 1 else "s"
    return f"{value} {unit}{suffix} ago"


@register.simple_tag
def get_connected_tooltip() -> str:
    factory = BrokerFactory()
    enabled_brokers = _get_enabled_brokers(factory)
    if not enabled_brokers:
        return "No brokers enabled"

    enabled_brokers = sorted(enabled_brokers, key=lambda broker: broker.short_name.lower())
    rows = [_build_broker_update_row(broker, factory) for broker in enabled_brokers]
    return f'<div class="broker-status-grid">{"".join(rows)}</div>'


def _get_enabled_brokers(factory: BrokerFactory) -> list[BrokerName]:
    enabled_brokers = []

    for broker_name in factory.get_available_brokers():
        config = factory.create_config(broker_name)
        if config and config.is_enabled():
            enabled_brokers.append(broker_name)

    return enabled_brokers


def _get_last_update_for_broker(broker_name: BrokerName, factory: BrokerFactory) -> datetime:
    update_service = factory.create_service(broker_name, ServiceType.UPDATE)
    if not update_service:
        LOGGER.warning(f"Update service unavailable for broker {broker_name}; using stale time fallback")
        return _get_stale_fallback_datetime()

    try:
        last_sync = update_service.get_last_sync()
        if isinstance(last_sync, datetime):
            return last_sync

        LOGGER.warning(f"No sync recorded yet for broker {broker_name}; using stale time fallback")
        return _get_stale_fallback_datetime()
    except Exception as error:
        LOGGER.warning(f"Failed to get last sync for broker {broker_name}: {error}; using stale time fallback")
        return _get_stale_fallback_datetime()


def _get_stale_fallback_datetime() -> datetime:
    return timezone.now() - timedelta(days=_STALE_FALLBACK_DAYS)


def _get_broker_config(broker_name: BrokerName, factory: BrokerFactory):
    return factory.create_config(broker_name)


def _build_broker_update_row(broker_name: BrokerName, factory: BrokerFactory) -> str:
    last_update = _get_last_update_for_broker(broker_name, factory)
    status_emoji = _get_update_status_emoji(broker_name, last_update, factory)
    local_time = timezone.localtime(last_update)
    now = timezone.localtime(timezone.now())
    time_text = f"Updated {_format_relative_time(now - local_time)}"

    return (
        f'<span class="broker-name">{broker_name.short_name}:</span>'
        f'<span class="status-emoji">{status_emoji}</span>'
        f"<span>{time_text}</span>"
    )


def _get_update_status_emoji(broker_name: BrokerName, last_update: datetime, factory: BrokerFactory) -> str:
    status_level = _get_update_status_level(broker_name, last_update, factory)
    if status_level == "ok":
        return "🟢"
    if status_level == "warning":
        return "🟡"
    return "🔴"


def _get_update_status_level(broker_name: BrokerName, last_update: datetime, factory: BrokerFactory) -> str:
    config = _get_broker_config(broker_name, factory)
    update_frequency_minutes = config.update_frequency_minutes if config else 0
    if update_frequency_minutes <= 0:
        return "error"

    now = timezone.localtime(timezone.now())
    local_time = timezone.localtime(last_update)
    delta_minutes = (now - local_time).total_seconds() / 60

    if delta_minutes <= update_frequency_minutes:
        return "ok"
    if delta_minutes <= update_frequency_minutes * 2:
        return "warning"
    return "error"


@register.simple_tag
def get_connected_status_level() -> str:
    factory = BrokerFactory()
    enabled_brokers = _get_enabled_brokers(factory)
    if not enabled_brokers:
        return "error"

    has_warning = False
    for broker in enabled_brokers:
        last_update = _get_last_update_for_broker(broker, factory)
        status_level = _get_update_status_level(broker, last_update, factory)
        if status_level == "error":
            return "error"
        if status_level == "warning":
            has_warning = True

    if has_warning:
        return "warning"
    return "ok"


@register.simple_tag
def get_connected_status_icon_class() -> str:
    status_level = get_connected_status_level()
    if status_level == "ok":
        return "text-success"
    if status_level == "warning":
        return "text-warning"
    return "text-danger"


@register.simple_tag
def get_connected_status_icon() -> str:
    status_level = get_connected_status_level()
    if status_level == "ok":
        return "bi-cloud-check-fill"
    if status_level == "warning":
        return "bi-cloud-fill"
    return "bi-cloud-slash-fill"
