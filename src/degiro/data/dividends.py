from degiro.data.account_overview import AccountOverviewData
from degiro.repositories.product_info_repository import ProductInfoRepository
from degiro.utils.degiro import DeGiro
from degiro.utils.localization import LocalizationUtility


class DividendsData:
    def __init__(self):
        self.account_overview = AccountOverviewData()
        self.product_info_repository = ProductInfoRepository()

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
            upcoming_payments = DeGiro.get_client().get_upcoming_payments(raw=True)
            if ("data" in upcoming_payments and upcoming_payments["data"]):
                for payment in upcoming_payments["data"]:
                    stock_name = payment["product"]
                    stock = self.product_info_repository.get_product_info_from_name(stock_name)
                    stock_symbol = stock["symbol"]

                    amount = float(payment["amount"])
                    currency = payment["currency"]
                    result.append({
                        "date": payment["payDate"],
                        "stockName": stock_name,
                        "stockSymbol": stock_symbol,
                        "currency": currency,
                        "change": amount,
                        "formatedChange": LocalizationUtility.format_money_value(value=amount, currency=currency),
                    })

            return result
        except Exception:
            return result
