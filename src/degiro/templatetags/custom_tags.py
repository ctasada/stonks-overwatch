from django import template

from degiro.repositories.cash_movements_repository import CashMovementsRepository
from degiro.repositories.company_profile_repository import CompanyProfileRepository
from degiro.repositories.product_info_repository import ProductInfoRepository
from degiro.repositories.product_quotations_repository import ProductQuotationsRepository
from degiro.services.degiro_service import DeGiroService
from degiro.services.portfolio import PortfolioService

register = template.Library()


@register.filter
def index(sequence, position):
    return sequence[position]


@register.inclusion_tag("total_overview.html")
def show_total_portfolio():

    portfolio = PortfolioService(
        cash_movements_repository=CashMovementsRepository(),
        company_profile_repository=CompanyProfileRepository(),
        degiro_service=DeGiroService(),
        product_info_repository=ProductInfoRepository(),
        product_quotation_repository=ProductQuotationsRepository(),
    )
    total_portfolio = portfolio.get_portfolio_total()

    # print(json.dumps(total_portfolio, indent = 4))

    return {"total_portfolio": total_portfolio}
