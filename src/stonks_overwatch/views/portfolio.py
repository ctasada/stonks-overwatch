from django.shortcuts import render
from django.views import View

from stonks_overwatch.services.portfolio_aggregator import PortfolioAggregatorService


class Portfolio(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.portfolio_aggregator = PortfolioAggregatorService()

    def get(self, request):
        portfolio = self.portfolio_aggregator.get_portfolio()
        stocks = [item for item in portfolio if item.get("productType") == "STOCK"]
        trackers = [item for item in portfolio if item.get("productType") == "ETF"]
        cash = [item for item in portfolio if item.get("productType") == "CASH"]
        crypto = [item for item in portfolio if item.get("productType") == "CRYPTO"]

        context = {
            "stocks": stocks,
            "show_stocks_columns": {
                "category": True,
                "sector": True,
                "shares": True,
                "price": True,
                "unrealized_gain": True,
            },
            "trackers": trackers,
            "show_trackers_columns": {
                "category": True,
                "sector": True,
                "shares": True,
                "price": True,
                "unrealized_gain": True,
            },
            "crypto": crypto,
            "show_crypto_columns": {
                "category": False,
                "sector": False,
                "shares": True,
                "price": True,
                "unrealized_gain": True,
            },
            "cash": cash,
            "show_cash_columns": {
                "category": False,
                "sector": False,
                "shares": False,
                "price": False,
                "unrealized_gain": False,
            },
        }

        return render(request, "portfolio.html", context)
