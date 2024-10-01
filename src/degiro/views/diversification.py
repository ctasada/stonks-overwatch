import logging

from currency_converter import CurrencyConverter
from django.shortcuts import render
from django.views import View

from degiro.repositories.cash_movements_repository import CashMovementsRepository
from degiro.repositories.company_profile_repository import CompanyProfileRepository
from degiro.repositories.product_info_repository import ProductInfoRepository
from degiro.repositories.product_quotations_repository import ProductQuotationsRepository
from degiro.services.degiro_service import DeGiroService
from degiro.services.portfolio import PortfolioService
from degiro.utils.localization import LocalizationUtility


class Diversification(View):
    logger = logging.getLogger("stocks_portfolio.dashboard.views")
    currency_converter = CurrencyConverter(fallback_on_missing_rate=True, fallback_on_wrong_date=True)

    def __init__(self):
        self.cash_movements_repository = CashMovementsRepository()
        self.company_profile_repository = CompanyProfileRepository()
        self.degiro_service = DeGiroService()
        self.product_info_repository = ProductInfoRepository()
        self.product_quotation_repository = ProductQuotationsRepository()

        self.portfolio = PortfolioService(
            cash_movements_repository=self.cash_movements_repository,
            company_profile_repository=self.company_profile_repository,
            degiro_service=self.degiro_service,
            product_info_repository=self.product_info_repository,
            product_quotation_repository=self.product_quotation_repository,
        )

    def get(self, request):
        portfolio = self.portfolio.get_portfolio()
        holdings = self._get_holdings(portfolio)
        sectors = self._get_sectors(portfolio)
        currencies = self._get_currencies(portfolio)
        countries = self._get_countries(portfolio)

        context = {
            "holdings": holdings,
            "sectors": sectors,
            "currencies": currencies,
            "countries": countries,
            "currencySymbol": LocalizationUtility.get_base_currency_symbol(),
        }

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
                stocks_table.append(
                    {
                        "name": stock["name"],
                        "portfolioSize": stock["portfolioSize"],
                        "formattedPortfolioSize": stock["formattedPortfolioSize"],
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

    def _get_sectors(self, portfolio: dict) -> dict:
        return self._get_data("sector", portfolio)

    def _get_currencies(self, portfolio: dict) -> dict:
        return self._get_data("productCurrency", portfolio)

    def _get_countries(self, portfolio: dict) -> dict:
        return self._get_data("country", portfolio)

    def _get_data(self, field_name: str, portfolio: dict) -> dict:
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
                    "value": value + stock["value"],
                    "portfolioSize": portfolio_size + stock["portfolioSize"],
                }
                max_percentage = max(max_percentage, data[name]["portfolioSize"])

        for key in data:
            portfolio_size = data[key]["portfolioSize"]
            data_table.append(
                {
                    "name": key,
                    "value": data[key]["value"],
                    "portfolioSize": portfolio_size,
                    "formattedPortfolioSize": f"{portfolio_size:.2%}",
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
