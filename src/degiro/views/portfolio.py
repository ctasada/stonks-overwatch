from django.shortcuts import render
from django.views import View

from degiro.repositories.cash_movements_repository import CashMovementsRepository
from degiro.repositories.company_profile_repository import CompanyProfileRepository
from degiro.repositories.product_info_repository import ProductInfoRepository
from degiro.repositories.product_quotations_repository import ProductQuotationsRepository
from degiro.services.degiro_service import DeGiroService
from degiro.services.portfolio import PortfolioService


class Portfolio(View):
    def __init__(self):
        self.cash_movements_repository = CashMovementsRepository()
        self.company_profile_repository = CompanyProfileRepository()
        self.degiro_service = DeGiroService()
        self.product_info_repository = ProductInfoRepository()
        self.product_quotation_repository = ProductQuotationsRepository()

        self.portfolio = PortfolioService(
            cash_movements_repository=self.cash_movements_repository,
            degiro_service=self.degiro_service,
            company_profile_repository=self.company_profile_repository,
            product_info_repository=self.product_info_repository,
            product_quotation_repository=self.product_quotation_repository,
        )

    def get(self, request):
        portfolio = self.portfolio.get_portfolio()
        stocks = [item for item in portfolio if item.get("productType") == "STOCK"]
        trackers = [item for item in portfolio if item.get("productType") == "ETF"]

        context = {
            "stocks": stocks,
            "trackers": trackers,
        }

        return render(request, "portfolio.html", context)
