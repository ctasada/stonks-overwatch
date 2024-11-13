import logging

from django.shortcuts import render
from django.views import View

from degiro.services.currency_converter_service import CurrencyConverterService
from degiro.services.degiro_service import DeGiroService
from degiro.services.portfolio import PortfolioService
from degiro.utils.localization import LocalizationUtility


class Diversification(View):
    logger = logging.getLogger("stocks_portfolio.dashboard.views")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.degiro_service = DeGiroService()
        self.currency_service = CurrencyConverterService()
        self.portfolio = PortfolioService(
            degiro_service=self.degiro_service,
        )

    def get(self, request):
        portfolio = self.portfolio.get_portfolio()
        product_types = self._get_product_types(portfolio)
        holdings = self._get_holdings(portfolio)
        sectors = self._get_sectors(portfolio)
        currencies = self._get_currencies(portfolio)
        countries = self._get_countries(portfolio)
        base_currency = self.degiro_service.get_base_currency()

        context = {
            "productTypes": product_types,
            "holdings": holdings,
            "sectors": sectors,
            "currencies": currencies,
            "countries": countries,
            "currencySymbol": LocalizationUtility.get_currency_symbol(base_currency),
        }

        return render(request, "diversification.html", context)

    def _get_holdings(self, portfolio: list[dict]) -> dict:
        stock_labels = []
        stock_values = []
        stocks_table = []
        portfolio = sorted(portfolio, key=lambda k: k["value"], reverse=True)

        max_percentage = portfolio[0]["portfolioSize"]

        for stock in portfolio:
            if stock["isOpen"]:
                stock_labels.append(stock["name"])
                stock_values.append(stock["baseCurrencyValue"])
                stocks_table.append(
                    {
                        "name": stock["name"],
                        "size": stock["portfolioSize"],
                        "formattedSize": stock["formattedPortfolioSize"],
                        "weight": (stock["portfolioSize"] / max_percentage) * 100,
                    }
                )

        return {
            "chart": {
                "labels": stock_labels,
                "values": stock_values,
            },
            "table": stocks_table,
        }

    def _get_product_types(self, portfolio: list[dict]) -> dict:
        return self._get_data("productType", portfolio)

    def _get_sectors(self, portfolio: list[dict]) -> dict:
        return self._get_data("sector", portfolio)

    def _get_currencies(self, portfolio: list[dict]) -> dict:
        return self._get_data("productCurrency", portfolio)

    def _get_countries(self, portfolio: list[dict]) -> dict:
        return self._get_data("country", portfolio)

    def _get_data(self, field_name: str, portfolio: list[dict]) -> dict:
        data_table = []
        data = {}

        max_percentage = 0.0

        for stock in portfolio:
            if stock["isOpen"]:
                name = stock[field_name]
                value = 0.0
                portfolio_size = 0.0
                if name in data:
                    value = data[name]["value"]
                    portfolio_size = data[name]["portfolioSize"]
                data[name] = {
                    "value": value + stock["baseCurrencyValue"],
                    "portfolioSize": portfolio_size + stock["portfolioSize"],
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
