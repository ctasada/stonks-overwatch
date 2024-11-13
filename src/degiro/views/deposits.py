import logging

from django.shortcuts import render
from django.views import View

from degiro.services.degiro_service import DeGiroService
from degiro.services.deposits import DepositsService
from degiro.services.portfolio import PortfolioService


class Deposits(View):
    logger = logging.getLogger("stocks_portfolio.deposits.views")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.degiro_service = DeGiroService()

        self.portfolio = PortfolioService(
            degiro_service=self.degiro_service,
        )

        self.deposits_data = DepositsService(
            degiro_service=self.degiro_service,
        )

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
