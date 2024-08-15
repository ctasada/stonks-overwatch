from django import template
from degiro.utils.degiro import DeGiro
from degiro.integration.portfolio import PortfolioData

register = template.Library()


@register.simple_tag
def clientrole():
    clientDetails = DeGiro.get_client_details()
    return clientDetails["data"]["clientRole"].capitalize()


@register.simple_tag
def username():
    clientDetails = DeGiro.get_client_details()
    return clientDetails["data"]["username"]


@register.filter
def index(sequence, position):
    return sequence[position]


@register.inclusion_tag("total_overview.html")
def show_total_portfolio():
    portfolio = PortfolioData()
    total_portfolio = portfolio.get_portfolio_total()

    # print(json.dumps(total_portfolio, indent = 4))

    return {"total_portfolio": total_portfolio}
