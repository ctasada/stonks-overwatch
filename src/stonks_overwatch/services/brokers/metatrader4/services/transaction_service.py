from typing import List

from currency_converter import CurrencyConverter

from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.core.interfaces.transaction_service import TransactionServiceInterface
from stonks_overwatch.services.brokers.metatrader4.repositories.metatrader4_repository import Metatrader4Repository
from stonks_overwatch.services.brokers.metatrader4.repositories.models import Metatrader4Trade
from stonks_overwatch.services.models import Transaction
from stonks_overwatch.utils.core.logger import StonksLogger


class TransactionService(BaseService, TransactionServiceInterface):
    def __init__(self, config=None):
        super().__init__(config)
        self.logger = StonksLogger.get_logger(__name__, "[METATRADER4|TRANSACTION]")
        self.repository = Metatrader4Repository()
        self.currency_converter = CurrencyConverter(fallback_on_missing_rate=True, fallback_on_wrong_date=True)
        self.currency = self.repository.get_account_currency()

    def get_transactions(self) -> List[Transaction]:
        """Return transaction data for this broker from the database."""
        self.logger.debug("Fetching transaction data from database")

        try:
            # Get closed trades from the database
            closed_trades = self.repository.get_closed_trades()

            transactions = []

            for trade in closed_trades:
                # Skip balance lines - they're not traditional transactions
                if trade.trade_type == "balance":
                    continue
                if not trade.close_price:
                    continue
                if trade.trade_type in ("buy stop", "buy limit"):
                    continue

                try:
                    # Create open and close transactions for each closed trade
                    trade_transaction = self._create_transaction(trade)
                    transactions.append(trade_transaction)
                except Exception as e:
                    self.logger.warning(f"Failed to create transactions from trade: {trade}, error: {e}")
                    continue

            # Sort by date descending (newest first)
            transactions.sort(key=lambda t: (t.date, t.time), reverse=True)

            self.logger.debug(f"Retrieved {len(transactions)} transactions from database")
            return transactions

        except Exception as e:
            self.logger.error(f"Failed to get transactions from database: {e}")
            raise

    def _create_transaction(self, trade: Metatrader4Trade) -> Transaction:
        # Parse dates and times
        open_date, open_time = self._split_datetime(trade.open_time) if trade.open_time else ("", "")
        close_date, close_time = self._split_datetime(trade.close_time) if trade.close_time else ("", "")

        # Determine buy/sell types
        trade_type = trade.trade_type.title() if trade.trade_type else "Unknown"

        # Calculate total fees (applied to close transaction)
        total_fees = -(float(trade.commission or 0) + float(trade.taxes or 0) + float(trade.swap or 0))

        return Transaction(
            name=trade.item,
            symbol=trade.item,
            date=close_date,
            time=close_time,
            buy_sell=trade_type,
            transaction_type="",
            price=float(trade.close_price),
            currency=self.currency,
            quantity=float(trade.size),
            total=float(trade.profit),
            total_currency=self.currency,
            total_in_base_currency=self.currency_converter.convert(
                float(trade.profit), self.currency, self.base_currency, trade.close_time
            ),
            base_currency=self.base_currency,
            fees=total_fees,
            fees_currency=self.currency,
        )

    def _split_datetime(self, dt) -> tuple[str, str]:
        """Split datetime object into date and time strings."""
        if not dt:
            return "", ""

        try:
            date_str = dt.strftime("%Y-%m-%d")
            time_str = dt.strftime("%H:%M:%S")
            return date_str, time_str
        except Exception:
            return "", ""
