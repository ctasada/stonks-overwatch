import logging
from typing import List

from django.shortcuts import render
from django.views import View

from stonks_overwatch.config.config import Config
from stonks_overwatch.services.models import PortfolioEntry
from stonks_overwatch.services.portfolio_aggregator import PortfolioAggregatorService
from stonks_overwatch.services.session_manager import SessionManager
from stonks_overwatch.utils.constants import Sector
from stonks_overwatch.utils.localization import LocalizationUtility


class Diversification(View):
    logger = logging.getLogger("stocks_portfolio.dashboard.views")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_currency = Config.default().base_currency
        self.portfolio = PortfolioAggregatorService()

    def get(self, request):
        selected_portfolio = SessionManager.get_selected_portfolio(request)
        portfolio = self.portfolio.get_portfolio(selected_portfolio)
        product_types = self._get_product_types(portfolio)
        positions = self._get_positions(portfolio)
        sectors = self._get_sectors(portfolio)
        currencies = self._get_currencies(portfolio)
        countries = self._get_countries(portfolio)

        context = {
            "productTypes": product_types,
            "positions": positions,
            "sectors": sectors,
            "currencies": currencies,
            "countries": countries,
            "currencySymbol": LocalizationUtility.get_currency_symbol(self.base_currency),
        }

        return render(request, "diversification.html", context)

    @staticmethod
    def _get_positions(portfolio: List[PortfolioEntry]) -> dict:
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
                        "formatted_size": stock.formatted_portfolio_size,
                        "weight": (stock.portfolio_size / max_percentage) * 100,
                        "logo": stock.symbol_url,
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
                elif field_name == "country":
                    name = stock.country.get_name() if stock.country else "Unknown Country"
                elif field_name == "product_currency":
                    symbol = LocalizationUtility.get_currency_symbol(stock.product_currency)
                    name = f"{symbol} {stock.product_currency}"
                elif field_name == "sector":
                    name = stock.sector.value if stock.sector else Sector.UNKNOWN.value
                else:
                    name =  getattr(stock, field_name)
                value = 0.0
                portfolio_size = 0.0
                if name in data:
                    value = data[name]["value"]
                    portfolio_size = data[name]["portfolio_size"]
                data[name] = {
                    "value": value + stock.base_currency_value,
                    "portfolio_size": portfolio_size + stock.portfolio_size,
                }
                max_percentage = max(max_percentage, data[name]["portfolio_size"])

        for key in data:
            portfolio_size = data[key]["portfolio_size"]
            data_table.append(
                {
                    "name": key,
                    "value": data[key]["value"],
                    "size": portfolio_size,
                    "formatted_size": f"{portfolio_size:.2%}",
                    "weight": (data[key]["portfolio_size"] / max_percentage) * 100,
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
