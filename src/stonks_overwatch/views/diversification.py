from typing import List

from django.shortcuts import render
from django.views import View

from stonks_overwatch.config.config import Config
from stonks_overwatch.services.aggregators.portfolio_aggregator import PortfolioAggregatorService
from stonks_overwatch.services.models import PortfolioEntry
from stonks_overwatch.services.utilities.session_manager import SessionManager
from stonks_overwatch.utils.core.localization import LocalizationUtility
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.domain.constants import ProductType, Sector


class Diversification(View):
    logger = StonksLogger.get_logger("stonks_overwatch.dashboard.views", "[VIEW|DIVERSIFICATION]")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_currency = Config.get_global().base_currency
        self.portfolio = PortfolioAggregatorService()

    def get(self, request):
        selected_portfolio = SessionManager.get_selected_portfolio(request)
        portfolio = self.portfolio.get_portfolio(selected_portfolio)
        product_types = self._get_product_types(portfolio)
        stocks = self._get_positions(portfolio, ProductType.STOCK)
        etfs = self._get_positions(portfolio, ProductType.ETF)
        crypto = self._get_crypto(portfolio)
        sectors = self._get_sectors(portfolio)
        currencies = self._get_currencies(portfolio)
        countries = self._get_countries(portfolio)

        context = {
            "productTypes": product_types,
            "stocks": stocks,
            "etfs": etfs,
            "crypto": crypto,
            "sectors": sectors,
            "currencies": currencies,
            "countries": countries,
            "currencySymbol": LocalizationUtility.get_currency_symbol(self.base_currency),
        }

        return render(request, "diversification.html", context)

    @staticmethod
    def _get_positions(portfolio: List[PortfolioEntry], product_type: ProductType) -> dict:
        # Filter by product_type and is_open first
        filtered = [entry for entry in portfolio if entry.is_open and entry.product_type == product_type]
        if not filtered:
            return {"chart": {"labels": [], "values": []}, "table": []}
        # Sort filtered by product_type_share descending
        filtered = sorted(filtered, key=lambda k: k.product_type_share, reverse=True)
        max_percentage = filtered[0].product_type_share
        # Prepare chart labels and values in the same order
        position_labels = [entry.formatted_name() for entry in filtered]
        position_values = [entry.base_currency_value for entry in filtered]
        # Build table without base_currency_value
        positions_table = [
            {
                "name": entry.formatted_name(),
                "product_type": entry.product_type.name,
                "symbol": entry.symbol,
                "size": entry.product_type_share,
                "formatted_size": entry.formatted_product_type_share,
                "weight": (entry.product_type_share / max_percentage) * 100 if max_percentage > 0 else 0.0,
                "formatted_value": entry.formatted_base_currency_value(),
            }
            for entry in filtered
        ]
        return {
            "chart": {
                "labels": position_labels,
                "values": position_values,
            },
            "table": positions_table,
        }

    @staticmethod
    def _get_crypto(portfolio: List[PortfolioEntry]) -> dict:
        # Filter and sort only open crypto positions
        filtered = [entry for entry in portfolio if entry.is_open and entry.product_type == ProductType.CRYPTO]
        if not filtered:
            return {"chart": {"labels": [], "values": []}, "table": []}
        filtered = sorted(filtered, key=lambda k: k.product_type_share, reverse=True)
        max_percentage = filtered[0].product_type_share
        crypto_labels = [stock.formatted_name() for stock in filtered]
        crypto_values = [stock.base_currency_value for stock in filtered]
        crypto_table = [
            {
                "name": stock.formatted_name(),
                "product_type": stock.product_type.name,
                "symbol": stock.symbol,
                "size": stock.product_type_share,
                "formatted_size": stock.formatted_product_type_share,
                "weight": (stock.product_type_share / max_percentage) * 100 if max_percentage > 0 else 0.0,
                "formatted_value": stock.formatted_base_currency_value(),
            }
            for stock in filtered
        ]
        return {
            "chart": {
                "labels": crypto_labels,
                "values": crypto_values,
            },
            "table": crypto_table,
        }

    def _get_product_types(self, portfolio: List[PortfolioEntry]) -> dict:
        return self._get_data("product_type", portfolio)

    def _get_sectors(self, portfolio: List[PortfolioEntry]) -> dict:
        return self._get_data("sector", portfolio)

    def _get_currencies(self, portfolio: List[PortfolioEntry]) -> dict:
        return self._get_data("product_currency", portfolio)

    def _get_countries(self, portfolio: List[PortfolioEntry]) -> dict:
        return self._get_data("country", portfolio)

    def _get_data(self, field_name: str, portfolio: List[PortfolioEntry]) -> dict:
        data_table = []
        data = {}

        # Only consider open positions for aggregation
        open_portfolio = [stock for stock in portfolio if stock.is_open]
        total_value = sum(stock.base_currency_value for stock in open_portfolio)
        max_percentage = 0.0

        for stock in open_portfolio:
            product_type = None
            symbol = None
            if field_name == "product_type":
                name = stock.product_type.value
            elif field_name == "country":
                if stock.product_type in [ProductType.CASH, ProductType.CRYPTO]:
                    # Neither cash nor crypto have a country
                    continue
                name = stock.country.get_name() if stock.country else "Unknown Country"
                symbol = stock.country.get_flag() if stock.country else None
                product_type = "country"
            elif field_name == "product_currency":
                symbol = Diversification.__get_currency_logo(stock.product_currency)
                name = stock.product_currency
                product_type = "cash"
            elif field_name == "sector":
                name = stock.sector.value if stock.sector else Sector.UNKNOWN.value
                symbol = stock.sector.to_logo() if stock.sector else Sector.UNKNOWN.to_logo()
                product_type = "sector"
            else:
                name = getattr(stock, field_name)

            value = 0.0
            if name in data:
                value = data[name]["value"]
            data[name] = {
                "value": value + stock.base_currency_value,
                "symbol": symbol,
                "product_type": product_type,
            }

        # Now calculate group product_type_share as group_value / total_value
        for key in data:
            group_value = data[key]["value"]
            product_type_share = (group_value / total_value) if total_value > 0 else 0.0
            data[key]["product_type_share"] = product_type_share
            max_percentage = max(max_percentage, product_type_share)

        for key in data:
            product_type_share = data[key]["product_type_share"]
            data_table.append(
                {
                    "name": key,
                    "value": data[key]["value"],
                    "formatted_value": LocalizationUtility.format_money_value(
                        value=data[key]["value"], currency=self.base_currency
                    ),
                    "size": product_type_share,
                    "formatted_size": f"{product_type_share:.2%}",
                    "weight": (product_type_share / max_percentage) * 100 if max_percentage > 0 else 0.0,
                    "symbol": data[key]["symbol"],
                    "product_type": data[key]["product_type"],
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

    @staticmethod
    def __get_currency_logo(currency: str) -> str:
        """Returns the actual currency symbol using the existing LocalizationUtility."""
        return LocalizationUtility.get_currency_symbol(currency)
