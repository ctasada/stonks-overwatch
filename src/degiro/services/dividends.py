import logging

from degiro.repositories.product_info_repository import ProductInfoRepository
from degiro.services.account_overview import AccountOverviewService
from degiro.services.degiro_service import DeGiroService
from degiro.utils.localization import LocalizationUtility


class DividendsService:
    logger = logging.getLogger("stocks_portfolio.dividends_service")

    def __init__(
        self,
        account_overview: AccountOverviewService,
        degiro_service: DeGiroService,
    ):
        self.account_overview = account_overview
        self.degiro_service = degiro_service

    def get_dividends(self):
        overview = self.account_overview.get_account_overview()

        dividends = []
        for transaction in overview:
            # We don't include 'Dividendbelasting' because the 'value' seems to already include the taxes
            if transaction["description"] in [
                "Dividend",
                "Dividendbelasting",
                "Vermogenswinst",
            ]:
                dividends.append(transaction)

        return dividends

    def get_upcoming_dividends(self):
        result = []
        try:
            upcoming_payments = self.degiro_service.get_client().get_upcoming_payments(raw=True)
            if "data" in upcoming_payments and upcoming_payments["data"]:
                for payment in upcoming_payments["data"]:
                    stock_name = payment["product"]
                    stock = ProductInfoRepository.get_product_info_from_name(stock_name)
                    stock_symbol = stock["symbol"]

                    amount = float(payment["amount"])
                    currency = payment["currency"]
                    result.append(
                        {
                            "date": payment["payDate"],
                            "stockName": stock_name,
                            "stockSymbol": stock_symbol,
                            "currency": currency,
                            "change": amount,
                            "formatedChange": LocalizationUtility.format_money_value(value=amount, currency=currency),
                        }
                    )

            return result
        except Exception as error:
            self.logger.error(error)
            return result
