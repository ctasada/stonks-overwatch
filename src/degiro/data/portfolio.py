from django.db import connection
from degiro.repositories.cash_movements_repository import CashMovementsRepository
from degiro.repositories.company_profile_repository import CompanyProfileRepository
from degiro.repositories.product_info_repository import ProductInfoRepository
from degiro.repositories.product_quotations_repository import ProductQuotationsRepository
from degiro.utils.db_utils import dictfetchall
from degiro.utils.localization import LocalizationUtility
from degiro.integration.portfolio import PortofolioIntegration

from currency_converter import CurrencyConverter

import logging


class PortfolioData:
    logger = logging.getLogger("stocks_portfolio.portfolio_data")
    currencyConverter = CurrencyConverter(
        fallback_on_missing_rate=True, fallback_on_wrong_date=True
    )

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
        portfolioTransactions = self.__get_porfolio_data()

        products_ids = [row['productId'] for row in portfolioTransactions]
        products_info = self.product_info_repository.get_products_info_raw(products_ids)

        # Get user's base currency
        baseCurrencySymbol = LocalizationUtility.get_base_currency_symbol()
        baseCurrency = LocalizationUtility.get_base_currency()

        myPortfolio = []

        for tmp in portfolioTransactions:
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
            breakEvenPrice = abs(tmp["totalPlusAllFeesInBaseCurrency"]) / tmp["size"]
            if currency != baseCurrency:
                price = self.currencyConverter.convert(
                    price, currency, baseCurrency
                )
                value = self.currencyConverter.convert(
                    value, currency, baseCurrency
                )
                breakEvenPrice = self.currencyConverter.convert(
                    breakEvenPrice, currency, baseCurrency
                )
                currency = baseCurrency

            formattedPrice = LocalizationUtility.format_money_value(
                value=price, currency=currency
            )
            formattedValue = LocalizationUtility.format_money_value(
                value=value, currencySymbol=baseCurrencySymbol
            )
            formattedBreakEvenPrice = LocalizationUtility.format_money_value(
                value=breakEvenPrice, currency=currency
            )

            unrealizedGain = (price - breakEvenPrice) * tmp["size"]
            formattedUnrealizedGain = LocalizationUtility.format_money_value(
                value=unrealizedGain, currency=currency
            )

            myPortfolio.append(
                dict(
                    name=info["name"],
                    symbol=info["symbol"],
                    sector=sector,
                    industry=industry,
                    shares=tmp["size"],
                    price=price,
                    breakEvenPrice=breakEvenPrice,
                    formattedPrice=formattedPrice,
                    formattedBreakEvenPrice=formattedBreakEvenPrice,  # GAK: Average Purchase Price
                    value=value,
                    formattedValue=formattedValue,
                    isOpen=True,
                    unrealizedGain=unrealizedGain,
                    formattedUnrealizedGain=formattedUnrealizedGain,
                    logoUrl=f"https://logos.stockanalysis.com/{info['symbol'].lower()}.svg",
                )
            )

        return sorted(myPortfolio, key=lambda k: k["symbol"])

    def __get_portfolio_total(self):
        # Calculate current value
        portfolio = self.get_portfolio()

        portfolioTotalValue = 0.0

        tmp_total_portfolio = {}
        for entry in portfolio:
            portfolioTotalValue += entry["value"]
            tmp_total_portfolio[entry["name"]] = entry["value"]

        baseCurrencySymbol = LocalizationUtility.get_base_currency_symbol()

        tmp_total_portfolio["totalDepositWithdrawal"] = self.cash_movements_repository.get_total_cash_deposits_raw()
        # FIXME: Calculate cash
        tmp_total_portfolio["totalCash"] = -1
        roi = (
            portfolioTotalValue / tmp_total_portfolio["totalDepositWithdrawal"] - 1
        ) * 100
        total_profit_loss = portfolioTotalValue - tmp_total_portfolio["totalDepositWithdrawal"]

        total_portfolio = {
            "total_pl": total_profit_loss,
            "total_pl_formatted": LocalizationUtility.format_money_value(
                value=total_profit_loss,
                currencySymbol=baseCurrencySymbol,
            ),
            "totalCash": LocalizationUtility.format_money_value(
                value=tmp_total_portfolio["totalCash"],
                currencySymbol=baseCurrencySymbol,
            ),
            "currentValue": LocalizationUtility.format_money_value(
                value=portfolioTotalValue, currencySymbol=baseCurrencySymbol
            ),
            "totalROI": roi,
            "totalROI_formatted": "{:,.2f}%".format(roi),
            "totalDepositWithdrawal": LocalizationUtility.format_money_value(
                value=tmp_total_portfolio["totalDepositWithdrawal"],
                currencySymbol=baseCurrencySymbol,
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
