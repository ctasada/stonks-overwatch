from django import template
from django.template import RequestContext
from django.utils import timezone

from stonks_overwatch.services.aggregators.portfolio_aggregator import PortfolioAggregatorService
from stonks_overwatch.services.brokers.degiro.client.degiro_client import DeGiroOfflineModeError, DeGiroService
from stonks_overwatch.services.brokers.degiro.services.update_service import UpdateService
from stonks_overwatch.services.models import dataclass_to_dict
from stonks_overwatch.services.utilities.session_manager import SessionManager
from stonks_overwatch.utils.core.localization import LocalizationUtility
from stonks_overwatch.utils.core.logger import StonksLogger

register = template.Library()


@register.filter
def index(sequence, position):
    return sequence[position]


@register.inclusion_tag("total_overview.html", takes_context=True)
def show_total_portfolio(context: RequestContext) -> dict:
    portfolio = PortfolioAggregatorService()
    selected_portfolio = SessionManager.get_selected_portfolio(context.request)
    total_portfolio = portfolio.get_portfolio_total(selected_portfolio)

    return {"total_portfolio": dataclass_to_dict(total_portfolio)}


@register.simple_tag
def is_connected_to_degiro() -> bool:
    try:
        # Check if DeGiro is enabled using unified factory
        from stonks_overwatch.core.factories.broker_factory import BrokerFactory

        broker_factory = BrokerFactory()
        degiro_config = broker_factory.create_config("degiro")

        if degiro_config and degiro_config.is_enabled():
            degiro_client = DeGiroService()
            is_connected = degiro_client.check_connection()
            if is_connected and degiro_client.is_maintenance_mode:
                return False
            return is_connected
        else:
            return False
    except DeGiroOfflineModeError:
        return False
    except Exception as error:
        StonksLogger.get_logger("stonks_overwatch.views.templates", "[CUSTOM_TAGS]").error(error)
        return False


@register.simple_tag
def last_import() -> str:
    last_update = UpdateService().get_last_import()

    local_time = timezone.localtime(last_update)

    return LocalizationUtility.format_date_time_from_date(local_time)


@register.simple_tag
def get_connected_tooltip() -> str:
    tooltip = ""
    if is_connected_to_degiro():
        tooltip += "DeGiro Online"
    else:
        tooltip += "DeGiro Offline"

    return tooltip + " <br> " + last_import()
