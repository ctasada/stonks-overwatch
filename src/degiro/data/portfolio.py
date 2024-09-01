import logging
import re

from currency_converter import CurrencyConverter
from degiro_connector.trading.models.account import UpdateOption, UpdateRequest
from django.db import connection

from degiro.repositories.cash_movements_repository import CashMovementsRepository
from degiro.repositories.company_profile_repository import CompanyProfileRepository
from degiro.repositories.product_info_repository import ProductInfoRepository
from degiro.repositories.product_quotations_repository import ProductQuotationsRepository
from degiro.utils.db_utils import dictfetchall
from degiro.utils.degiro import DeGiro
from degiro.utils.localization import LocalizationUtility


class PortfolioData:
    logger = logging.getLogger("stocks_portfolio.portfolio_data")
    currency_converter = CurrencyConverter(fallback_on_missing_rate=True, fallback_on_wrong_date=True)

    def __init__(self):
        self.product_info_repository = ProductInfoRepository()
        self.company_profile_repository = CompanyProfileRepository()
        self.product_quotation_repository = ProductQuotationsRepository()
        self.cash_movements_repository = CashMovementsRepository()

    def get_portfolio(self):
        portfolio_transactions = self.__get_porfolio_products()

        products_ids = [row["product_id"] for row in portfolio_transactions]
        products_info = self.__get_products_info(products_ids=products_ids)

        # Get user's base currency
        base_currency_symbol = LocalizationUtility.get_base_currency_symbol()
        base_currency = LocalizationUtility.get_base_currency()

        my_portfolio = []
        portfolio_total_value = 0.0

        for tmp in portfolio_transactions:
            info = products_info[tmp["product_id"]]
            company_profile = self.company_profile_repository.get_company_profile_raw(info["isin"])
            sector = "Unknown"
            industry = "Unknown"
            if company_profile.get("data"):
                sector = company_profile["data"]["sector"]
                industry = company_profile["data"]["industry"]

            currency = info["currency"]
            price = self.product_quotation_repository.get_product_price(tmp["product_id"])
            value = tmp["size"] * price
            break_even_price = tmp["break_even_price"]
            if currency != base_currency:
                price = self.currency_converter.convert(price, currency, base_currency)
                value = self.currency_converter.convert(value, currency, base_currency)
                break_even_price = self.currency_converter.convert(break_even_price, currency, base_currency)
                currency = base_currency

            formatted_price = LocalizationUtility.format_money_value(value=price, currency=currency)
            formatted_value = LocalizationUtility.format_money_value(value=value, currency_symbol=base_currency_symbol)
            formatted_break_even_price = LocalizationUtility.format_money_value(
                value=break_even_price, currency=currency
            )
            is_open = tmp["size"] != 0.0 and tmp["value"] != 0.0
            unrealized_gain = (price - break_even_price) * tmp["size"]
            formatted_unrealized_gain = LocalizationUtility.format_money_value(value=unrealized_gain, currency=currency)
            percentage_gain = 0.0
            if value > 0:
                percentage_gain = unrealized_gain / (value - unrealized_gain)

            portfolio_total_value += value

            my_portfolio.append(
                {
                    "name": info["name"],
                    "symbol": info["symbol"],
                    "sector": sector,
                    "industry": industry,
                    "shares": tmp["size"],
                    "price": price,
                    "formattedPrice": formatted_price,
                    "breakEvenPrice": break_even_price,
                    "formattedBreakEvenPrice": formatted_break_even_price,  # GAK: Average Purchase Price
                    "value": value,
                    "formattedValue": formatted_value,
                    "isOpen": is_open,
                    "unrealizedGain": unrealized_gain,
                    "formattedUnrealizedGain": formatted_unrealized_gain,
                    "percentageGain": f"{percentage_gain:.2%}",
                    "logoUrl": f"https://logos.stockanalysis.com/{info['symbol'].lower()}.svg",
                    "portfolioSize": 0.0, # Calculated in the next loop
                    "formattedPortfolioSize": 0.0, # Calculated in the next loop
                }
            )

        # Calculate Stock Portfolio Size
        for entry in my_portfolio:
            size = entry["value"] / portfolio_total_value
            entry["portfolioSize"] = size
            entry["formattedPortfolioSize"] = f"{size:.2%}"

        return sorted(my_portfolio, key=lambda k: k["symbol"])

    def get_portfolio_total(self):
        # Calculate current value
        portfolio = self.get_portfolio()

        portfolio_total_value = 0.0

        tmp_total_portfolio = {}
        for entry in portfolio:
            portfolio_total_value += entry["value"]
            tmp_total_portfolio[entry["name"]] = entry["value"]

        base_currency_symbol = LocalizationUtility.get_base_currency_symbol()

        tmp_total_portfolio["totalDepositWithdrawal"] = self.cash_movements_repository.get_total_cash_deposits_raw()
        tmp_total_portfolio["totalCash"] = self.cash_movements_repository.get_total_cash()

        # Try to get the data directly from DeGiro, so we get up-to-date values
        realtime_total_portfolio = self.__get_realtime_portfolio_total()
        if realtime_total_portfolio:
            tmp_total_portfolio = realtime_total_portfolio

        roi = (portfolio_total_value / tmp_total_portfolio["totalDepositWithdrawal"] - 1) * 100
        total_profit_loss = portfolio_total_value - tmp_total_portfolio["totalDepositWithdrawal"]

        total_portfolio = {
            "total_pl": total_profit_loss,
            "total_pl_formatted": LocalizationUtility.format_money_value(
                value=total_profit_loss,
                currency_symbol=base_currency_symbol,
            ),
            "totalCash": tmp_total_portfolio["totalCash"],
            "totalCash_formatted": LocalizationUtility.format_money_value(
                value=tmp_total_portfolio["totalCash"],
                currency_symbol=base_currency_symbol,
            ),
            "currentValue": portfolio_total_value,
            "currentValue_formatted": LocalizationUtility.format_money_value(
                value=portfolio_total_value, currency_symbol=base_currency_symbol
            ),
            "totalROI": roi,
            "totalROI_formatted": "{:,.2f}%".format(roi),
            "totalDepositWithdrawal": LocalizationUtility.format_money_value(
                value=tmp_total_portfolio["totalDepositWithdrawal"],
                currency_symbol=base_currency_symbol,
            ),
        }

        return total_portfolio

    def __get_realtime_portfolio_total(self) -> dict:
        try:
            update = DeGiro.get_client().get_update(
                request_list=[
                    UpdateRequest(option=UpdateOption.TOTAL_PORTFOLIO, last_updated=0),
                ],
                raw=True,
            )
            tmp_total_portfolio = {}
            for value in update["totalPortfolio"]["value"]:
                if value.get("value") is not None:
                    tmp_total_portfolio[value["name"]] = value["value"]

            return tmp_total_portfolio
        except Exception:
            return None

    def __get_porfolio_products(self) -> dict:
        try:
            update = DeGiro.get_client().get_update(
                request_list=[
                    UpdateRequest(option=UpdateOption.PORTFOLIO, last_updated=0),
                ],
                raw=True,
            )
            my_portfolio = []
            # ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
            for tmp in update["portfolio"]["value"]:
                # Some products have ids like 'FLATEX_EUR' or 'FLATEX_USD'
                if tmp["id"].isnumeric():
                    portfolio = {}
                    for value in tmp["value"]:
                        if value.get("value") is not None:
                            if value["name"] == "id":
                                key = "product_id"
                            else:
                                key = camel_to_snake_case(value["name"])
                            portfolio[key] = value["value"]

                    my_portfolio.append(portfolio)
            return my_portfolio

        except Exception:
            logging.exception("Cannot connecto to DeGiro, getting last known data")
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT product_id,
                        SUM(quantity) AS size,
                        SUM(total_plus_all_fees_in_base_currency) as total_plus_all_fees_in_base_currency,
                        ABS(SUM(total_plus_all_fees_in_base_currency) / SUM(quantity)) AS break_evenPrice
                    FROM degiro_transactions
                    GROUP BY product_id
                    HAVING SUM(quantity) > 0;
                    """
                )
                return dictfetchall(cursor)

    def __get_products_info(self, products_ids):
        try:
            return DeGiro.get_products_info(products_ids)
        except Exception:
            logging.exception("Cannot connecto to DeGiro, getting last known data")
            return self.product_info_repository.get_products_info_raw(products_ids)

    def __get_company_profile(self, product_isin) -> dict:
        try:
            company_profile = DeGiro.get_client().get_company_profile(
                product_isin=product_isin,
                raw=True,
            )

            return company_profile
        except Exception:
            logging.exception("Cannot connecto to DeGiro, getting last known data")
            return self.company_profile_repository.get_company_profile_raw(isin=product_isin)


def camel_to_snake_case(camel_str):
    # Insert an underscore before each uppercase letter
    snake_str = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", camel_str)
    # Handle cases where there are multiple uppercase letters together (e.g., HTTPResponse)
    snake_str = re.sub("([a-z0-9])([A-Z])", r"\1_\2", snake_str)
    # Convert the entire string to lowercase
    return snake_str.lower()
