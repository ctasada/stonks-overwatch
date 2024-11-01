from django.shortcuts import render
from django.views import View

from degiro.services.degiro_service import DeGiroService
from degiro.services.portfolio import PortfolioService


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
            "trackers": trackers,
            "cash": cash,
        }

        return render(request, "portfolio.html", context)
