from datetime import datetime
from typing import List, Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.core.interfaces.transaction_service import TransactionServiceInterface
from stonks_overwatch.services.brokers.bitvavo.client.bitvavo_client import BitvavoService
from stonks_overwatch.services.brokers.bitvavo.repositories.assets_repository import AssetsRepository
from stonks_overwatch.services.brokers.bitvavo.repositories.transactions_repository import TransactionsRepository
from stonks_overwatch.services.models import Transaction
from stonks_overwatch.utils.core.localization import LocalizationUtility


class TransactionsService(BaseService, TransactionServiceInterface):
    TIME_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
    TIME_FORMAT = "%H:%M:%S"

    def __init__(self, config: Optional[BaseConfig] = None):
        super().__init__(config)
        self.bitvavo_service = BitvavoService()

    # Note: base_currency property is inherited from BaseService and handles
    # dependency injection automatically

    def get_transactions(self) -> List[Transaction]:
        # FETCH TRANSACTIONS DATA
        transactions_history = TransactionsRepository.get_transactions_raw()

        # DISPLAY PRODUCTS_INFO
        my_transactions = []
        for transaction in transactions_history:
            if transaction["type"] == "deposit":
                continue

            asset = AssetsRepository.get_asset(transaction["receivedCurrency"])

            my_transactions.append(
                Transaction(
                    name=asset["name"],
                    symbol=transaction["receivedCurrency"],
                    date=TransactionsService.format_date(transaction["executedAt"]),
                    time=TransactionsService.format_time(transaction["executedAt"]),
                    buy_sell=self.__convert_buy_sell(transaction["type"]),
                    transaction_type=self.__transaction_type(transaction["type"]),
                    price=LocalizationUtility.format_money_value(
                        transaction.get("priceAmount") or 0.0,
                        currency=transaction.get("priceCurrency") or self.base_currency,
                    ),
                    quantity=transaction["receivedAmount"],
                    total=LocalizationUtility.format_money_value(
                        value=transaction.get("sentAmount") or 0.0,
                        currency=transaction.get("sentCurrency") or self.base_currency,
                    ),
                    total_in_base_currency=LocalizationUtility.format_money_value(
                        value=transaction.get("sentAmount") or 0.0,
                        currency=transaction.get("sentCurrency") or self.base_currency,
                    ),
                    fees=LocalizationUtility.format_money_value(
                        value=transaction.get("feesAmount") or 0.0,
                        currency=transaction.get("feesCurrency") or self.base_currency,
                    ),
                )
            )

        return sorted(my_transactions, key=lambda k: (k.date, k.time), reverse=True)

    @staticmethod
    def __transaction_type(type: str) -> str:
        if type == "buy":
            return ""

        return type.capitalize()

    @staticmethod
    def __convert_buy_sell(buy_sell: str) -> str:
        if buy_sell in ["buy", "staking"]:
            return "Buy"
        elif buy_sell == "sell":
            return "Sell"

        return "Unknown"

    @staticmethod
    def parse_date(value: str) -> datetime:
        """
        Parses a date time string to a datetime object.
        """
        try:
            return datetime.strptime(value, TransactionsService.TIME_DATE_FORMAT)
        except ValueError as e:
            raise ValueError(
                f"Invalid date format: {value}. Expected format is {TransactionsService.TIME_DATE_FORMAT}."
            ) from e

    @staticmethod
    def format_date(value: str | datetime) -> str:
        """
        Formats a date time string to date string.
        """
        if isinstance(value, str):
            time = TransactionsService.parse_date(value)
        elif isinstance(value, datetime):
            time = value
        else:
            raise TypeError(f"Unsupported type: {type(value)}. Expected str or datetime.")

        return time.strftime(LocalizationUtility.DATE_FORMAT)

    @staticmethod
    def format_time(value: str | datetime) -> str:
        """
        Formats a date time string to time string.
        """
        if isinstance(value, str):
            time = TransactionsService.parse_date(value)
        elif isinstance(value, datetime):
            time = value
        else:
            raise TypeError(f"Unsupported type: {type(value)}. Expected str or datetime.")

        return time.strftime(LocalizationUtility.TIME_FORMAT)
