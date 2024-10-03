from django import template

from degiro.services.degiro_service import DeGiroService
from degiro.services.portfolio import PortfolioService

register = template.Library()


@register.filter
def index(sequence, position):
    return sequence[position]


@register.inclusion_tag("total_overview.html")
def show_total_portfolio():
    portfolio = PortfolioService(
        degiro_service=DeGiroService(),
    )
    total_portfolio = portfolio.get_portfolio_total()

    # print(json.dumps(total_portfolio, indent = 4))

    return {"total_portfolio": total_portfolio}
