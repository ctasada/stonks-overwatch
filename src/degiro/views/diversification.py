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

        context = {
            "holdings": holdings,
            "sectors": sectors,
            "currencies": currencies,
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
            sectors_table.append(
                {
                    "name": key,
                    "value": sectors[key]["value"],
                    "portfolioSize": portfolio_size,
                    "formattedPortfolioSize": f"{portfolio_size:.2%}",
                    "weight": (sectors[key]["portfolioSize"] / max_percentage) * 100,
                }
            )
        sectors_table = sorted(sectors_table, key=lambda k: k["value"], reverse=True)

        sector_labels = [row["name"] for row in sectors_table]
        sector_values = [row["value"] for row in sectors_table]

        return {
            "chart": {
                "labels": sector_labels,
                "values": sector_values,
            },
            "table": sectors_table,
        }

    def _get_currencies(self, portfolio: dict) -> dict:
        currencies_table = []
        currencies = {}

        max_percentage = 0.0

        for stock in portfolio:
            if stock["isOpen"]:
                currency_name = stock["productCurrency"]
                currency_value = 0.0
                portfolio_size = 0.0
                if currency_name in currencies:
                    currency_value = currencies[currency_name]["value"]
                    portfolio_size = currencies[currency_name]["portfolioSize"]
                currencies[currency_name] = {
                    "value": currency_value + stock["value"],
                    "portfolioSize": portfolio_size + stock["portfolioSize"],
                }
                max_percentage = max(max_percentage, currencies[currency_name]["portfolioSize"])

        for key in currencies:
            portfolio_size = currencies[key]["portfolioSize"]
            currencies_table.append(
                {
                    "name": key,
                    "value": currencies[key]["value"],
                    "portfolioSize": portfolio_size,
                    "formattedPortfolioSize": f"{portfolio_size:.2%}",
                    "weight": (currencies[key]["portfolioSize"] / max_percentage) * 100,
                }
            )
        currencies_table = sorted(currencies_table, key=lambda k: k["value"], reverse=True)

        currencies_labels = [row["name"] for row in currencies_table]
        currencies_values = [row["value"] for row in currencies_table]

        return {
            "chart": {
                "labels": currencies_labels,
                "values": currencies_values,
            },
            "table": currencies_table,
        }
