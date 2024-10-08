from django import template

from degiro.services.degiro_service import DeGiroService
from degiro.services.portfolio import PortfolioService

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
