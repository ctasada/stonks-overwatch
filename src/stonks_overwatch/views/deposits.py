import logging

from django.shortcuts import render
from django.views import View

from stonks_overwatch.services.deposits_aggregator import DepositsAggregatorService
from stonks_overwatch.services.portfolio_aggregator import PortfolioAggregatorService


class Deposits(View):
    logger = logging.getLogger("stocks_portfolio.deposits.views")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.deposits_aggregator = DepositsAggregatorService()
        self.portfolio_aggregator = PortfolioAggregatorService()

    def get(self, request):
        data = self.deposits_aggregator.cash_deposits_history()
        cash_contributions = [{"x": item["date"], "y": item["total_deposit"]} for item in data]

        deposits = self.deposits_aggregator.get_cash_deposits()
        total_portfolio = self.portfolio_aggregator.get_portfolio_total()

        context = {
            "total_deposits": total_portfolio.total_deposit_withdrawal_formatted,
            "deposits": deposits,
            "deposit_growth": {"value": cash_contributions},
        }

        return render(request, "deposits.html", context)
