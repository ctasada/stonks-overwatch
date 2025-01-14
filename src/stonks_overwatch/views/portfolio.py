
from django.shortcuts import render
from django.views import View

from stonks_overwatch.services.portfolio_aggregator import PortfolioAggregatorService
from stonks_overwatch.utils.constants import ProductType


class Portfolio(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.portfolio_aggregator = PortfolioAggregatorService()

    def get(self, request):
        portfolio = self.portfolio_aggregator.get_portfolio()

        stocks = [item for item in portfolio if item.product_type == ProductType.STOCK]
        trackers = [item for item in portfolio if item.product_type == ProductType.ETF]
        cash = [item for item in portfolio if item.product_type == ProductType.CASH]
        cryptos = [item for item in portfolio if item.product_type == ProductType.CRYPTO]

        context = {
            "stocks": [stock.to_dict() for stock in stocks],
            "show_stocks_columns": {
                "category": True,
                "sector": True,
                "shares": True,
                "price": True,
                "unrealized_gain": True,
            },
            "trackers": [tracker.to_dict() for tracker in trackers],
            "show_trackers_columns": {
                "category": True,
                "sector": True,
                "shares": True,
                "price": True,
                "unrealized_gain": True,
            },
            "crypto": [crypto.to_dict() for crypto in cryptos],
            "show_crypto_columns": {
                "category": False,
                "sector": False,
                "shares": True,
                "price": True,
                "unrealized_gain": True,
            },
            "cash": [currency.to_dict() for currency in cash],
            "show_cash_columns": {
                "category": False,
                "sector": False,
                "shares": False,
                "price": False,
                "unrealized_gain": False,
            },
        }

        return render(request, "portfolio.html", context)
