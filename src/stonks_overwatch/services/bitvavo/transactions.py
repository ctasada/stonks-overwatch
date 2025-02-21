from datetime import datetime
from typing import List

from stonks_overwatch.config.config import Config
from stonks_overwatch.services.bitvavo.bitvavo_service import BitvavoService
from stonks_overwatch.services.models import Transaction
from stonks_overwatch.utils.localization import LocalizationUtility


class TransactionsService:
    TIME_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
    TIME_FORMAT = "%H:%M:%S"

    def __init__(self):
        self.bitvavo_service = BitvavoService()
        self.base_currency = Config.default().base_currency

    def get_transactions(self) -> List[Transaction]:
        # FETCH TRANSACTIONS DATA
        transactions_history = self.bitvavo_service.account_history()

        # DISPLAY PRODUCTS_INFO
        my_transactions = []
        for transaction in transactions_history["items"]:
            if transaction["type"] == "deposit":
                continue

            asset = self.bitvavo_service.assets(transaction["receivedCurrency"])

            my_transactions.append(
                Transaction(
                    name=asset["name"],
                    symbol=transaction["receivedCurrency"],
                    date=TransactionsService.format_date(transaction["executedAt"]),
                    time=TransactionsService.format_time(transaction["executedAt"]),
                    buy_sell=self.__convert_buy_sell(transaction["type"]),
                    transaction_type=self.__transaction_type(transaction["type"]),
                    price=LocalizationUtility.format_money_value(
                        transaction.get("priceAmount", 0.0),
                        currency=transaction.get("priceCurrency", self.base_currency)
                    ),
                    quantity=transaction["receivedAmount"],
                    total=LocalizationUtility.format_money_value(
                        value=transaction.get("sentAmount", 0.0),
                        currency=transaction.get("sentCurrency", self.base_currency)
                    ),
                    total_in_base_currency=LocalizationUtility.format_money_value(
                        value=transaction.get("sentAmount", 0.0),
                        currency=transaction.get("sentCurrency", self.base_currency)
                    ),
                    fees=LocalizationUtility.format_money_value(
                        value=transaction.get("feesAmount", 0.0),
                        currency=transaction.get("feesCurrency", self.base_currency)
                    ),
                )
            )

        return sorted(my_transactions, key=lambda k: (k.date, k.time), reverse=True)

    @staticmethod
    def __transaction_type(type: str) -> str:
        if type == "buy":
            return ""

        return  type.capitalize()

    @staticmethod
    def __convert_buy_sell(buy_sell: str) -> str:
        if buy_sell in ["buy", "staking"]:
            return "Buy"
        elif buy_sell == "sell":
            return "Sell"

        return "Unknown"


    @staticmethod
    def format_date(value: str) -> str:
        """
        Formats a date time string to date string.
        """
        time = datetime.strptime(value, TransactionsService.TIME_DATE_FORMAT)
        return time.strftime(LocalizationUtility.DATE_FORMAT)

    @staticmethod
    def format_time(value: str) -> str:
        """
        Formats a date time string to time string.
        """
        time = datetime.strptime(value, TransactionsService.TIME_DATE_FORMAT)
        return time.strftime(LocalizationUtility.TIME_FORMAT)
