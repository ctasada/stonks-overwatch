from typing import List

from stonks_overwatch.core.interfaces import TransactionServiceInterface
from stonks_overwatch.services.brokers.ibkr.client.constants import TransactionType
from stonks_overwatch.services.brokers.ibkr.client.ibkr_service import IbkrService
from stonks_overwatch.services.brokers.ibkr.repositories.positions_repository import PositionsRepository
from stonks_overwatch.services.brokers.ibkr.repositories.transactions_repository import TransactionsRepository
from stonks_overwatch.services.models import Transaction
from stonks_overwatch.utils.core.localization import LocalizationUtility
from stonks_overwatch.utils.core.logger import StonksLogger


class TransactionsService(TransactionServiceInterface):
    logger = StonksLogger.get_logger("stonks_overwatch.account_overview_data", "IBKR|ACCOUNT_OVERVIEW")

    def __init__(self, ibkr_service: IbkrService):
        self.ibkr_service = ibkr_service
        self.base_currency = ibkr_service.account.currency

    def get_transactions(self) -> List[Transaction]:
        self.logger.debug("Get Transactions")
        # FETCH TRANSACTIONS DATA
        transactions_history = TransactionsRepository.get_transactions_raw()

        products_ids = []

        # ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
        for transaction in transactions_history:
            products_ids.append(int(transaction["conid"]))

        # Remove duplicates from the list
        products_ids = list(set(products_ids))
        products_info = PositionsRepository.get_products_info_raw(products_ids)

        # DISPLAY PRODUCTS_INFO
        my_transactions = []
        for transaction in transactions_history:
            info = products_info[transaction["conid"]]

            # Some transactions, like dividends, may not have a price, in those cases we use the total amount
            price = transaction["pr"]
            total = transaction["amt"]
            if price is None:
                price = total

            my_transactions.append(
                Transaction(
                    name=info["name"],
                    symbol=info["ticker"],
                    date=transaction["date"].strftime(LocalizationUtility.DATE_FORMAT),
                    time=transaction["date"].strftime(LocalizationUtility.TIME_FORMAT),
                    buy_sell=self.__convert_buy_sell(transaction["type"]),
                    transaction_type=transaction["type"],
                    price=LocalizationUtility.format_money_value(price, currency=transaction["cur"]),
                    quantity=transaction["qty"],
                    # FIXME: Validate if amt is always in the same currency as the product
                    total=LocalizationUtility.format_money_value(value=total, currency=transaction["cur"]),
                    total_in_base_currency=LocalizationUtility.format_money_value(
                        value=total,
                        currency=self.base_currency,
                    ),
                    # FIXME: Find out how to obtain the transaction fees
                    fees=LocalizationUtility.format_money_value(value=0.0, currency=self.base_currency),
                )
            )

        return sorted(my_transactions, key=lambda k: (k.date, k.time), reverse=True)

    @staticmethod
    def __convert_buy_sell(transaction_type: str) -> str:
        if transaction_type == TransactionType.BUY.to_string():
            return "Buy"
        elif transaction_type == TransactionType.SELL.to_string():
            return "Sell"

        return "Unknown"
