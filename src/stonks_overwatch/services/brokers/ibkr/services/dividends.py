from typing import List

from stonks_overwatch.core.interfaces import DividendServiceInterface
from stonks_overwatch.services.brokers.ibkr.client.constants import TransactionType
from stonks_overwatch.services.brokers.ibkr.client.ibkr_service import IbkrService
from stonks_overwatch.services.brokers.ibkr.repositories.positions_repository import PositionsRepository
from stonks_overwatch.services.brokers.ibkr.repositories.transactions_repository import TransactionsRepository
from stonks_overwatch.services.models import Dividend, DividendType
from stonks_overwatch.utils.core.logger import StonksLogger


class DividendsService(DividendServiceInterface):
    logger = StonksLogger.get_logger("stonks_overwatch.dividends_service", "[DEGIRO|DIVIDENDS]")

    def __init__(self, ibkr_service: IbkrService):
        self.ibkr_service = ibkr_service
        self.base_currency = ibkr_service.account.currency

    def get_dividends(self) -> List[Dividend]:
        dividends = self._get_dividends()

        # FIXME: We need to add support for Upcoming and Forecasted Dividends
        joined_dividends = dividends

        return sorted(joined_dividends, key=lambda k: k.payment_date)

    def _get_dividends(self) -> List[Dividend]:
        # FETCH TRANSACTIONS DATA
        transactions_history = TransactionsRepository.get_transactions_raw()

        products_ids = []

        # ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
        for transaction in transactions_history:
            products_ids.append(int(transaction["conid"]))

        # Remove duplicates from the list
        products_ids = list(set(products_ids))
        products_info = PositionsRepository.get_products_info_raw(products_ids)

        dividends = []

        for transaction in transactions_history:
            if transaction["type"] == TransactionType.DIVIDEND_PAYMENT.to_string():
                info = products_info[transaction["conid"]]

                # The transaction amount is in the base currency, so no need to convert it
                amount = float(transaction["amt"])
                currency = self.base_currency

                dividends.append(
                    Dividend(
                        dividend_type=DividendType.PAID,
                        payment_date=transaction["date"],
                        stock_name=info["name"],
                        stock_symbol=info["ticker"],
                        currency=currency,
                        amount=amount,
                        # FIXME: Add support for taxes
                        taxes=0.0,
                    )
                )

        return dividends
