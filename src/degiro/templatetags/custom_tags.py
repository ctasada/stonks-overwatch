from django import template

from degiro.services.degiro_service import DeGiroService
from degiro.services.portfolio import PortfolioService
from degiro.services.update_service import UpdateService
from degiro.utils.localization import LocalizationUtility

register = template.Library()


@register.filter
def index(sequence, position):
    return sequence[position]


@register.inclusion_tag("total_overview.html")
def show_total_portfolio() -> dict:
    portfolio = PortfolioService(
        degiro_service=DeGiroService(),
    )
    total_portfolio = portfolio.get_portfolio_total()

    return {"total_portfolio": total_portfolio}

@register.simple_tag
def is_connected_to_degiro() -> bool:
    return DeGiroService().check_connection()

@register.simple_tag
def last_import() -> str:
    last_update = UpdateService().get_last_import()

    return LocalizationUtility.format_date_time_from_date(last_update)

@register.simple_tag
def get_connected_tooltip() -> str:
    tooltip = ""
    if is_connected_to_degiro():
        tooltip += "DeGiro Online"
    else:
        tooltip += "DeGiro Offline"

    return tooltip + " <br> " + last_import()
