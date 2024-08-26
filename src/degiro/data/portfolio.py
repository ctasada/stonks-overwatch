from django.db import connection
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

    def get_portfolio(self):
        try:
            return self.portfolioIntegration.get_portfolio()
        except Exception:
            logging.exception("Cannot connecto to DeGiro, getting last known data")
            return self.__get_portfolio

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
            value = LocalizationUtility.format_money_value(
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
                    formattedValue=value,
                    isOpen=True,
                    unrealizedGain=unrealizedGain,
                    formattedUnrealizedGain=formattedUnrealizedGain,
                    logoUrl=f"https://logos.stockanalysis.com/{info['symbol'].lower()}.svg",
                )
            )

        return sorted(myPortfolio, key=lambda k: k["symbol"])

    # FIXME: Get rid of this wrapper. Should call DeGiro or calculate locally if fails
    def get_portfolio_total(self):
        return self.portfolioIntegration.get_portfolio_total()

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
