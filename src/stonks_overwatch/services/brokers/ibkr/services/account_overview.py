from typing import List, Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.services.brokers.ibkr.client.constants import TransactionType
from stonks_overwatch.services.brokers.ibkr.repositories.positions_repository import PositionsRepository
from stonks_overwatch.services.brokers.ibkr.repositories.transactions_repository import TransactionsRepository
from stonks_overwatch.services.models import AccountOverview
from stonks_overwatch.utils.core.logger import StonksLogger


class AccountOverviewService(BaseService):
    logger = StonksLogger.get_logger("stonks_overwatch.account_overview_data", "IBKR|ACCOUNT_OVERVIEW")

    def __init__(self, config: Optional[BaseConfig] = None):
        super().__init__(config)

    def get_account_overview(self) -> List[AccountOverview]:
        self.logger.debug("Get Account Overview")

        # FETCH TRANSACTIONS DATA
        transactions_history = TransactionsRepository.get_transactions_raw()

        products_ids = []

        # ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
        for transaction in transactions_history:
            products_ids.append(int(transaction["conid"]))

        # Remove duplicates from the list
        products_ids = list(set(products_ids))
        products_info = PositionsRepository.get_products_info_raw(products_ids)
        overview = []
        for transaction in transactions_history:
            info = products_info[transaction["conid"]]

            description = self.__get_description(transaction, info)

            stock_name = info["name"]
            stock_symbol = info["ticker"]

            overview.append(
                AccountOverview(
                    datetime=transaction["date"],
                    value_datetime=transaction["date"],
                    stock_name=stock_name,
                    stock_symbol=stock_symbol,
                    description=description,
                    type=transaction["type"],
                    currency=transaction["cur"],
                    change=transaction.get("amt", 0.0),
                )
            )

        return overview

    def __get_description(self, transaction: dict, product: dict) -> str:
        """
        Generate a description for the transaction based on its type and product information.
        """
        if transaction["type"] == TransactionType.BUY.to_string():
            price = transaction["pr"]
            currency = transaction["cur"]
            quantity = transaction["qty"]

            return f"Bought {quantity} @ {price} {currency} {product['ticker']} ({product['name']})"
        elif transaction["type"] == "SELL":
            price = transaction["pr"]
            currency = transaction["cur"]
            quantity = transaction["qty"]

            return f"Sold {quantity} @ {price} {currency} {product['ticker']} ({product['name']})"
        elif transaction["type"] == TransactionType.DIVIDEND_PAYMENT.to_string():
            return f"Received dividend from {product['ticker']} ({product['name']})"
        else:
            return f"Transaction of type {transaction['type']} for {product['ticker']} ({product['name']})"
