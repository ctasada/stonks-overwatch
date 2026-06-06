"""Alpaca transaction service implementation."""

from typing import List, Optional

from stonks_overwatch.config.alpaca import AlpacaConfig
from stonks_overwatch.core.interfaces.transaction_service import TransactionServiceInterface
from stonks_overwatch.services.brokers.alpaca.repositories.orders_repository import OrdersRepository
from stonks_overwatch.services.brokers.alpaca.services.alpaca_base_service import AlpacaBaseService
from stonks_overwatch.services.models import Transaction
from stonks_overwatch.utils.core.localization import LocalizationUtility
from stonks_overwatch.utils.core.logger import StonksLogger


class TransactionService(AlpacaBaseService, TransactionServiceInterface):
    """
    Transaction service for Alpaca Markets.

    Reads filled orders from the local DB (synced by UpdateService) and
    maps them to the shared Transaction model.  All prices and totals from
    Alpaca are in USD and are converted to base_currency using the historical
    exchange rate on each order's fill date.
    """

    logger = StonksLogger.get_logger("stonks_overwatch.alpaca.transaction", "[ALPACA|TRANSACTION]")

    def __init__(self, config: Optional[AlpacaConfig] = None):
        """
        Initialize the transaction service.

        Args:
            config: Optional Alpaca configuration (injected by factory if not provided)
        """
        super().__init__(config)

    def get_transactions(self) -> List[Transaction]:
        """
        Retrieve filled orders as Transaction objects.

        Returns:
            List of Transaction objects sorted newest first
        """
        self.logger.debug("Getting Alpaca transactions")
        orders = OrdersRepository.get_filled_orders()
        transactions: List[Transaction] = []

        for order in orders:
            filled_qty = float(order.filled_qty or 0)
            filled_price_usd = float(order.filled_avg_price or 0)
            total_usd = filled_qty * filled_price_usd

            fill_date = order.filled_at.date() if order.filled_at else None

            date_str = ""
            time_str = ""
            if order.filled_at:
                date_str = LocalizationUtility.format_date_from_date(order.filled_at)
                time_str = LocalizationUtility.format_time_from_date(order.filled_at)

            total_base = self._to_base(total_usd, on_date=fill_date)
            price_base = self._to_base(filled_price_usd, on_date=fill_date)

            transactions.append(
                Transaction(
                    name=order.symbol,
                    symbol=order.symbol,
                    date=date_str,
                    time=time_str,
                    buy_sell="Buy" if order.side == "buy" else "Sell",
                    transaction_type=order.order_type.capitalize() if order.order_type else "",
                    price=price_base,
                    currency=self.base_currency,
                    quantity=filled_qty,
                    total=total_base,
                    total_currency=self.base_currency,
                    total_in_base_currency=total_base,
                    base_currency=self.base_currency,
                    fees=0.0,
                    fees_currency=self.base_currency,
                )
            )

        return transactions
