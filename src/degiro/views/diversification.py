import logging

from currency_converter import CurrencyConverter
from django.shortcuts import render
from django.views import View

from degiro.data.portfolio import PortfolioData
from degiro.utils.localization import LocalizationUtility


class Diversification(View):
    logger = logging.getLogger("stocks_portfolio.dashboard.views")
    currency_converter = CurrencyConverter(fallback_on_missing_rate=True, fallback_on_wrong_date=True)

    def __init__(self):
        self.portfolio = PortfolioData()

    def get(self, request):
        portfolio = self.portfolio.get_portfolio()
        holdings = self._get_holdings(portfolio)
        industries = self._get_industries(portfolio)

        context = {
            "holdings": holdings,
            "industries": industries,
            "currencySymbol": LocalizationUtility.get_base_currency_symbol(),
        }

        # FIXME: Simplify this response
        return render(request, "diversification.html", context)

    def _get_holdings(self, portfolio: dict) -> dict:
        stock_labels = []
        stock_values = []
        portfolio = sorted(portfolio, key=lambda k: k["value"], reverse=True)

        for stock in portfolio:
            if stock["isOpen"]:
                stock_labels.append(stock["name"])
                stock_values.append(stock["value"])

        return {
            "labels": stock_labels,
            "values": stock_values,
        }

    def _get_industries(self, portfolio: dict) -> dict:
        sector_labels = []
        sector_values = []
        sectors = {}

        for stock in portfolio:
            if stock["isOpen"]:
                sector_name = stock["sector"]
                sectors[sector_name] = sectors.get(sector_name, 0) + stock["value"]

        for key in sectors:
            sector_labels.append(key)
            sector_values.append(sectors[key])

        return {
            "labels": sector_labels,
            "values": sector_values,
        }
