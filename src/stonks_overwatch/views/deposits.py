
from django.shortcuts import render
from django.views import View

from stonks_overwatch.services.deposits_aggregator import DepositsAggregatorService
from stonks_overwatch.services.portfolio_aggregator import PortfolioAggregatorService
from stonks_overwatch.services.session_manager import SessionManager
from stonks_overwatch.utils.logger import StonksLogger


class Deposits(View):
    logger = StonksLogger.get_logger("stocks_portfolio.deposits.views", "VIEW|DEPOSITS")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.deposits_aggregator = DepositsAggregatorService()
        self.portfolio_aggregator = PortfolioAggregatorService()

    def get(self, request):
        selected_portfolio = SessionManager.get_selected_portfolio(request)
        self.logger.debug(f"Selected Portfolio: {selected_portfolio}")

        data = self.deposits_aggregator.cash_deposits_history(selected_portfolio)
        cash_contributions = [{"x": item["date"], "y": item["total_deposit"]} for item in data]

        deposits = self.deposits_aggregator.get_cash_deposits(selected_portfolio)
        total_portfolio = self.portfolio_aggregator.get_portfolio_total(selected_portfolio)

        context = {
            "total_deposits": total_portfolio.total_deposit_withdrawal_formatted,
            "deposits": deposits,
            "deposit_growth": {"value": cash_contributions},
        }

        return render(request, "deposits.html", context)
