from django.views import View
from django.shortcuts import render

from degiro.data.deposits import DepositsData
from degiro.integration.portfolio import PortfolioData

import logging


class Deposits(View):
    logger = logging.getLogger("stocks_portfolio.deposits.views")

    def __init__(self):
        self.portfolio = PortfolioData()
        self.deposits_data = DepositsData()

    def get(self, request):
        data = self.deposits_data.cash_deposits_history()
        cash_contributions = [{'x': item['date'], 'y': item['total_deposit']} for item in data]

        deposits = self.deposits_data.get_cash_deposits()
        total_portfolio = self.portfolio.get_portfolio_total()

        context = {
            "total_deposits": total_portfolio['totalDepositWithdrawal'],
            "deposits": deposits,
            "deposit_growth": {"value": cash_contributions},
        }

        return render(request, "deposits.html", context)
