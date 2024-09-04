from django.shortcuts import render
from django.views import View

from degiro.data.portfolio import PortfolioData


class Portfolio(View):
    def __init__(self):
        self.portfolio = PortfolioData()

    def get(self, request):
        portfolio = self.portfolio.get_portfolio()
        stocks = [item for item in portfolio if item.get("productType") == "STOCK"]
        trackers = [item for item in portfolio if item.get("productType") == "ETF"]

        context = {
            "stocks": stocks,
            "trackers": trackers,
        }

        return render(request, "portfolio.html", context)
