import logging

from currency_converter import CurrencyConverter
from django.db import connection

from degiro.integration.portfolio import PortofolioIntegration
from degiro.repositories.cash_movements_repository import CashMovementsRepository
from degiro.repositories.company_profile_repository import CompanyProfileRepository
from degiro.repositories.product_info_repository import ProductInfoRepository
from degiro.repositories.product_quotations_repository import ProductQuotationsRepository
from degiro.utils.db_utils import dictfetchall
from degiro.utils.localization import LocalizationUtility


class PortfolioData:
    logger = logging.getLogger("stocks_portfolio.portfolio_data")
    currency_converter = CurrencyConverter(fallback_on_missing_rate=True, fallback_on_wrong_date=True)

    def __init__(self):
        self.product_info_repository = ProductInfoRepository()
        self.company_profile_repository = CompanyProfileRepository()
        self.product_quotation_repository = ProductQuotationsRepository()
        self.portfolioIntegration = PortofolioIntegration()
        self.cash_movements_repository = CashMovementsRepository()

    def get_portfolio(self):
        try:
            return self.portfolioIntegration.get_portfolio()
        except Exception:
            logging.exception("Cannot connecto to DeGiro, getting last known data")
            return self.__get_portfolio()

    def get_portfolio_total(self):
        try:
            return self.portfolioIntegration.get_portfolio_total()
        except Exception:
            logging.exception("Cannot connecto to DeGiro, getting last known data")
            return self.__get_portfolio_total()

    def __get_portfolio(self):
        portfolio_transactions = self.__get_porfolio_data()

        products_ids = [row["productId"] for row in portfolio_transactions]
        products_info = self.product_info_repository.get_products_info_raw(products_ids)

        # Get user's base currency
        base_currency_symbol = LocalizationUtility.get_base_currency_symbol()
        base_currency = LocalizationUtility.get_base_currency()

        my_portfolio = []

        for tmp in portfolio_transactions:
            info = products_info[tmp["productId"]]
            company_profile = company_profile = self.company_profile_repository.get_company_profile_raw(info["isin"])
            sector = "Unknown"
            industry = "Unknown"
            if company_profile.get("data"):
                sector = company_profile["data"]["sector"]
                industry = company_profile["data"]["industry"]

            currency = info["currency"]
            price = self.product_quotation_repository.get_product_price(tmp["productId"])
            value = tmp["size"] * price
            break_even_price = abs(tmp["totalPlusAllFeesInBaseCurrency"]) / tmp["size"]
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

            unrealized_gain = (price - break_even_price) * tmp["size"]
            formatted_unrealized_gain = LocalizationUtility.format_money_value(value=unrealized_gain, currency=currency)

            my_portfolio.append(
                {
                    "name": info["name"],
                    "symbol": info["symbol"],
                    "sector": sector,
                    "industry": industry,
                    "shares": tmp["size"],
                    "price": price,
                    "breakEvenPrice": break_even_price,
                    "formattedPrice": formatted_price,
                    "formattedBreakEvenPrice": formatted_break_even_price,  # GAK: Average Purchase Price
                    "value": value,
                    "formattedValue": formatted_value,
                    "isOpen": True,
                    "unrealizedGain": unrealized_gain,
                    "formattedUnrealizedGain": formatted_unrealized_gain,
                    "logoUrl": f"https://logos.stockanalysis.com/{info['symbol'].lower()}.svg",
                }
            )

        return sorted(my_portfolio, key=lambda k: k["symbol"])

    def __get_portfolio_total(self):
        # Calculate current value
        portfolio = self.get_portfolio()

        portfolio_total_value = 0.0

        tmp_total_portfolio = {}
        for entry in portfolio:
            portfolio_total_value += entry["value"]
            tmp_total_portfolio[entry["name"]] = entry["value"]

        base_currency_symbol = LocalizationUtility.get_base_currency_symbol()

        tmp_total_portfolio["totalDepositWithdrawal"] = self.cash_movements_repository.get_total_cash_deposits_raw()
        # FIXME: Calculate cash
        tmp_total_portfolio["totalCash"] = -1
        roi = (portfolio_total_value / tmp_total_portfolio["totalDepositWithdrawal"] - 1) * 100
        total_profit_loss = portfolio_total_value - tmp_total_portfolio["totalDepositWithdrawal"]

        total_portfolio = {
            "total_pl": total_profit_loss,
            "total_pl_formatted": LocalizationUtility.format_money_value(
                value=total_profit_loss,
                currency_symbol=base_currency_symbol,
            ),
            "totalCash": LocalizationUtility.format_money_value(
                value=tmp_total_portfolio["totalCash"],
                currency_symbol=base_currency_symbol,
            ),
            "currentValue": LocalizationUtility.format_money_value(
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

    def __get_porfolio_data(self) -> dict:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT productId, SUM(quantity) AS size,
                    SUM(totalPlusAllFeesInBaseCurrency) as totalPlusAllFeesInBaseCurrency
                FROM degiro_transactions
                GROUP BY productId
                HAVING SUM(quantity) > 0;
                """
            )
            return dictfetchall(cursor)
