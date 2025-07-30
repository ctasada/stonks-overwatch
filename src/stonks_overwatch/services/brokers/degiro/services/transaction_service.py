from typing import List, Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.core.interfaces.transaction_service import TransactionServiceInterface
from stonks_overwatch.services.brokers.degiro.client.constants import TransactionType
from stonks_overwatch.services.brokers.degiro.client.degiro_client import DeGiroService
from stonks_overwatch.services.brokers.degiro.repositories.product_info_repository import ProductInfoRepository
from stonks_overwatch.services.brokers.degiro.repositories.transactions_repository import TransactionsRepository
from stonks_overwatch.services.models import Transaction
from stonks_overwatch.utils.core.localization import LocalizationUtility


class TransactionsService(BaseService, TransactionServiceInterface):
    def __init__(
        self,
        degiro_service: Optional[DeGiroService] = None,
        config: Optional[BaseConfig] = None,
    ):
        super().__init__(config)
        self.degiro_service = degiro_service or DeGiroService()

    # Note: base_currency property is inherited from BaseService and handles
    # dependency injection automatically

    def get_transactions(self) -> List[Transaction]:
        # FETCH TRANSACTIONS DATA
        transactions_history = TransactionsRepository.get_transactions_raw()

        products_ids = []

        # ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
        for transaction in transactions_history:
            products_ids.append(int(transaction["productId"]))

        # Remove duplicates from the list
        products_ids = list(set(products_ids))
        products_info = ProductInfoRepository.get_products_info_raw(products_ids)

        # DISPLAY PRODUCTS_INFO
        my_transactions = []
        for transaction in transactions_history:
            info = products_info[transaction["productId"]]

            fees = transaction["totalPlusFeeInBaseCurrency"] - transaction["totalInBaseCurrency"]

            my_transactions.append(
                Transaction(
                    name=info["name"],
                    symbol=info["symbol"],
                    date=transaction["date"].strftime(LocalizationUtility.DATE_FORMAT),
                    time=transaction["date"].strftime(LocalizationUtility.TIME_FORMAT),
                    buy_sell=self.__convert_buy_sell(transaction["buysell"]),
                    transaction_type=TransactionType.from_int(transaction["transactionTypeId"]).to_string(),
                    price=LocalizationUtility.format_money_value(transaction["price"], currency=info["currency"]),
                    quantity=transaction["quantity"],
                    total=LocalizationUtility.format_money_value(value=transaction["total"], currency=info["currency"]),
                    total_in_base_currency=LocalizationUtility.format_money_value(
                        value=transaction["totalInBaseCurrency"],
                        currency=self.base_currency,
                    ),
                    fees=LocalizationUtility.format_money_value(value=fees, currency=self.base_currency),
                )
            )

        return sorted(my_transactions, key=lambda k: (k.date, k.time), reverse=True)

    @staticmethod
    def __convert_buy_sell(buy_sell: str) -> str:
        if buy_sell == "B":
            return "Buy"
        elif buy_sell == "S":
            return "Sell"

        return "Unknown"
