import logging
from typing import List

from django.shortcuts import render
from django.views import View

from stonks_overwatch.config import Config
from stonks_overwatch.services.models import PortfolioEntry
from stonks_overwatch.services.portfolio_aggregator import PortfolioAggregatorService
from stonks_overwatch.utils.localization import LocalizationUtility


class Diversification(View):
    logger = logging.getLogger("stocks_portfolio.dashboard.views")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_currency = Config.default().base_currency
        self.portfolio = PortfolioAggregatorService()

    def get(self, request):
        portfolio = self.portfolio.get_portfolio()
        product_types = self._get_product_types(portfolio)
        holdings = self._get_holdings(portfolio)
        sectors = self._get_sectors(portfolio)
        currencies = self._get_currencies(portfolio)
        countries = self._get_countries(portfolio)

        context = {
            "productTypes": product_types,
            "holdings": holdings,
            "sectors": sectors,
            "currencies": currencies,
            "countries": countries,
            "currencySymbol": LocalizationUtility.get_currency_symbol(self.base_currency),
        }

        return render(request, "diversification.html", context)

    @staticmethod
    def _get_holdings(portfolio: List[PortfolioEntry]) -> dict:
        stock_labels = []
        stock_values = []
        stocks_table = []
        portfolio = sorted(portfolio, key=lambda k: k.value, reverse=True)

        max_percentage = portfolio[0].portfolio_size

        for stock in portfolio:
            if stock.is_open:
                stock_labels.append(stock.name)
                stock_values.append(stock.base_currency_value)
                stocks_table.append(
                    {
                        "name": stock.name,
                        "size": stock.portfolio_size,
                        "formattedSize": stock.formatted_portfolio_size,
                        "weight": (stock.portfolio_size / max_percentage) * 100,
                    }
                )

        return {
            "chart": {
                "labels": stock_labels,
                "values": stock_values,
            },
            "table": stocks_table,
        }

    def _get_product_types(self, portfolio: List[PortfolioEntry]) -> dict:
        return self._get_data("product_type", portfolio)

    def _get_sectors(self, portfolio: List[PortfolioEntry]) -> dict:
        return self._get_data("sector", portfolio)

    def _get_currencies(self, portfolio: List[PortfolioEntry]) -> dict:
        return self._get_data("product_currency", portfolio)

    def _get_countries(self, portfolio: List[PortfolioEntry]) -> dict:
        return self._get_data("country", portfolio)

    @staticmethod
    def _get_data(field_name: str, portfolio: List[PortfolioEntry]) -> dict:
        data_table = []
        data = {}

        max_percentage = 0.0

        for stock in portfolio:
            if stock.is_open:
                if field_name == "product_type":
                    name = stock.product_type.value
                else:
                    name =  getattr(stock, field_name)
                value = 0.0
                portfolio_size = 0.0
                if name in data:
                    value = data[name]["value"]
                    portfolio_size = data[name]["portfolioSize"]
                data[name] = {
                    "value": value + stock.base_currency_value,
                    "portfolioSize": portfolio_size + stock.portfolio_size,
                }
                max_percentage = max(max_percentage, data[name]["portfolioSize"])

        for key in data:
            portfolio_size = data[key]["portfolioSize"]
            data_table.append(
                {
                    "name": key,
                    "value": data[key]["value"],
                    "size": portfolio_size,
                    "formattedSize": f"{portfolio_size:.2%}",
                    "weight": (data[key]["portfolioSize"] / max_percentage) * 100,
                }
            )
        data_table = sorted(data_table, key=lambda k: k["value"], reverse=True)

        labels = [row["name"] for row in data_table]
        values = [row["value"] for row in data_table]

        return {
            "chart": {
                "labels": labels,
                "values": values,
            },
            "table": data_table,
        }
