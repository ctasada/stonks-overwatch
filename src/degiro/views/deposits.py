import logging

from django.shortcuts import render
from django.views import View

from degiro.repositories.cash_movements_repository import CashMovementsRepository
from degiro.repositories.company_profile_repository import CompanyProfileRepository
from degiro.repositories.product_info_repository import ProductInfoRepository
from degiro.repositories.product_quotations_repository import ProductQuotationsRepository
from degiro.services.degiro_service import DeGiroService
from degiro.services.deposits import DepositsService
from degiro.services.portfolio import PortfolioService


class Deposits(View):
    logger = logging.getLogger("stocks_portfolio.deposits.views")

    def __init__(self):
        self.cash_movements_repository = CashMovementsRepository()
        self.company_profile_repository = CompanyProfileRepository()
        self.degiro_service = DeGiroService()
        self.product_info_repository = ProductInfoRepository()
        self.product_quotation_repository = ProductQuotationsRepository()

        self.portfolio = PortfolioService(
            cash_movements_repository=self.cash_movements_repository,
            company_profile_repository=self.company_profile_repository,
            degiro_service=self.degiro_service,
            product_info_repository=self.product_info_repository,
            product_quotation_repository=self.product_quotation_repository,
        )

        self.deposits_data = DepositsService(cash_movements_repository=self.cash_movements_repository)

    def get(self, request):
        data = self.deposits_data.cash_deposits_history()
        cash_contributions = [{"x": item["date"], "y": item["total_deposit"]} for item in data]

        deposits = self.deposits_data.get_cash_deposits()
        total_portfolio = self.portfolio.get_portfolio_total()

        context = {
            "total_deposits": total_portfolio["totalDepositWithdrawal"],
            "deposits": deposits,
            "deposit_growth": {"value": cash_contributions},
        }

        return render(request, "deposits.html", context)
