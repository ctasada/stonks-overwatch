
from django import template
from django.template import RequestContext
from django.utils import timezone

from stonks_overwatch.config.config import Config
from stonks_overwatch.services.degiro.degiro_service import DeGiroService
from stonks_overwatch.services.degiro.update_service import UpdateService
from stonks_overwatch.services.models import dataclass_to_dict
from stonks_overwatch.services.portfolio_aggregator import PortfolioAggregatorService
from stonks_overwatch.services.session_manager import SessionManager
from stonks_overwatch.utils.localization import LocalizationUtility

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
    if Config.default().is_degiro_enabled():
        return DeGiroService().check_connection()
    else:
        return False

@register.simple_tag
def last_import() -> str:
    last_update = UpdateService().get_last_import()

    local_time =  timezone.localtime(last_update)

    return LocalizationUtility.format_date_time_from_date(local_time)

@register.simple_tag
def get_connected_tooltip() -> str:
    tooltip = ""
    if is_connected_to_degiro():
        tooltip += "DeGiro Online"
    else:
        tooltip += "DeGiro Offline"

    return tooltip + " <br> " + last_import()
