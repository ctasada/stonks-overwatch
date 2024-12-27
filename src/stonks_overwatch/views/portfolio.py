from django.shortcuts import render
from django.views import View

from stonks_overwatch.services.degiro.degiro_service import DeGiroService
from stonks_overwatch.services.degiro.portfolio import PortfolioService


class Portfolio(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.degiro_service = DeGiroService()

        self.portfolio = PortfolioService(
            degiro_service=self.degiro_service,
        )

    def get(self, request):
        portfolio = self.portfolio.get_portfolio()
        stocks = [item for item in portfolio if item.get("productType") == "STOCK"]
        trackers = [item for item in portfolio if item.get("productType") == "ETF"]
        cash = [item for item in portfolio if item.get("productType") == "CASH"]

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
