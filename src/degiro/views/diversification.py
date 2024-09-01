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
        sectors = self._get_sectors(portfolio)

        context = {
            "holdings": holdings,
            "sectors": sectors,
            "currencySymbol": LocalizationUtility.get_base_currency_symbol(),
        }

        # FIXME: Simplify this response
        return render(request, "diversification.html", context)

    def _get_holdings(self, portfolio: dict) -> dict:
        stock_labels = []
        stock_values = []
        stocks_table = []
        portfolio = sorted(portfolio, key=lambda k: k["value"], reverse=True)

        max_percentage = portfolio[0]["portfolioSize"]

        for stock in portfolio:
            if stock["isOpen"]:
                stock_labels.append(stock["name"])
                stock_values.append(stock["value"])
                stocks_table.append({
                    "name": stock["name"],
                    "portfolioSize": stock["portfolioSize"],
                    "formattedPortfolioSize": stock["formattedPortfolioSize"],
                    "weight": (stock["portfolioSize"] / max_percentage) * 100,
                })

        return {
            "chart": {
                "labels": stock_labels,
                "values": stock_values,
            },
            "table": stocks_table
        }

    def _get_sectors(self, portfolio: dict) -> dict:
        sectors_table = []
        sectors = {}

        max_percentage = 0.0

        for stock in portfolio:
            if stock["isOpen"]:
                sector_name = stock["sector"]
                sector_value = 0.0
                portfolio_size = 0.0
                if sector_name in sectors:
                    sector_value = sectors[sector_name]["value"]
                    portfolio_size = sectors[sector_name]["portfolioSize"]
                sectors[sector_name] = {
                    "value": sector_value + stock["value"],
                    "portfolioSize": portfolio_size + stock["portfolioSize"],
                }
                max_percentage = max(max_percentage, sectors[sector_name]["portfolioSize"])

        for key in sectors:
            portfolio_size = sectors[key]["portfolioSize"]
            sectors_table.append({
                "name": key,
                "value": sectors[key]["value"],
                "portfolioSize": portfolio_size,
                "formattedPortfolioSize": f"{portfolio_size:.2%}",
                "weight": (sectors[key]["portfolioSize"] / max_percentage) * 100,
            })
        sectors_table = sorted(sectors_table, key=lambda k: k["value"], reverse=True)

        sector_labels = [row["name"] for row in sectors_table]
        sector_values = [row["value"] for row in sectors_table]

        return {
            "chart": {
                "labels": sector_labels,
                "values": sector_values,
            },
            "table": sectors_table
        }
