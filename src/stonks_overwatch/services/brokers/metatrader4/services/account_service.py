from datetime import datetime, timezone
from typing import List

from stonks_overwatch.core.interfaces.account_service import AccountServiceInterface
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.services.brokers.metatrader4.repositories.metatrader4_repository import Metatrader4Repository
from stonks_overwatch.services.models import AccountOverview
from stonks_overwatch.utils.core.logger import StonksLogger


class AccountService(BaseService, AccountServiceInterface):
    def __init__(self, config=None):
        super().__init__(config)
        self.logger = StonksLogger.get_logger(__name__, "[METATRADER4|ACCOUNT]")
        self.repository = Metatrader4Repository()
        self.currency = self.repository.get_account_currency()

    def get_account_overview(self) -> List[AccountOverview]:
        """Return account overview data for this broker from the database."""
        self.logger.debug("Fetching account overview from database")

        try:
            # Get all closed trades (including balance entries) from the database
            closed_trades = self.repository.get_closed_trades()

            overview = []

            for trade in closed_trades:
                try:
                    entry = self._create_account_overview(trade)
                    overview.append(entry)
                except Exception as e:
                    self.logger.warning(f"Failed to create account overview from trade: {trade}, error: {e}")
                    continue

            # Sort by datetime descending (newest first)
            tz_aware_min = datetime.min.replace(tzinfo=timezone.utc)
            overview.sort(key=lambda x: x.datetime if x.datetime else tz_aware_min, reverse=True)

            self.logger.debug(f"Retrieved {len(overview)} account overview entries from database")
            return overview

        except Exception as e:
            self.logger.error(f"Failed to get account overview from database: {e}")
            raise

    def _create_account_overview(self, trade) -> AccountOverview:
        """Create AccountOverview from a database trade record."""
        # Calculate net change based on trade type
        if trade.trade_type == "balance":
            # For balance entries, profit holds the deposit/withdrawal amount
            change = float(trade.profit) if trade.profit else 0.0
            description = trade.description or "Deposit/Withdrawal"
            stock_name = "Cash"
            stock_symbol = ""
            # Use open_time for balance entries
            dt = trade.open_time
        else:
            # For trade entries, calculate net change including all fees
            profit = float(trade.profit) if trade.profit else 0.0
            commission = float(trade.commission) if trade.commission else 0.0
            taxes = float(trade.taxes) if trade.taxes else 0.0
            swap = float(trade.swap) if trade.swap else 0.0

            change = profit + commission + taxes + swap
            description = f"{trade.trade_type} {trade.item}"
            stock_name = trade.item or ""
            stock_symbol = trade.item or ""
            # Use close_time for completed trades
            dt = trade.close_time or trade.open_time

        return AccountOverview(
            datetime=dt,
            value_datetime=dt,
            stock_name=stock_name,
            stock_symbol=stock_symbol,
            description=description,
            type=trade.trade_type or "Unknown",
            currency=self.base_currency or self.currency,
            change=change,
        )
