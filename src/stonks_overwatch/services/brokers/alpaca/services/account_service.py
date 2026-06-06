"""Alpaca account service implementation."""

from typing import List, Optional

from django.utils import timezone

from stonks_overwatch.config.alpaca import AlpacaConfig
from stonks_overwatch.core.interfaces.account_service import AccountServiceInterface
from stonks_overwatch.services.brokers.alpaca.client.alpaca_client import AlpacaClient
from stonks_overwatch.services.brokers.alpaca.services.alpaca_base_service import AlpacaBaseService
from stonks_overwatch.services.models import AccountOverview
from stonks_overwatch.utils.core.logger import StonksLogger


class AccountService(AlpacaBaseService, AccountServiceInterface):
    """
    Account service for Alpaca Markets.

    Fetches live account data from the Alpaca Trading API and returns
    a list of AccountOverview entries suitable for the dashboard.
    All monetary values are converted from USD to the user's base currency.
    """

    logger = StonksLogger.get_logger("stonks_overwatch.alpaca.account", "[ALPACA|ACCOUNT]")

    def __init__(self, config: Optional[AlpacaConfig] = None):
        """
        Initialize the account service.

        Args:
            config: Optional Alpaca configuration (injected by factory if not provided)
        """
        super().__init__(config)
        self.alpaca_client = AlpacaClient()

    def get_account_overview(self) -> List[AccountOverview]:
        """
        Retrieve account overview entries for the dashboard.

        Each key account metric (equity, cash, buying power, P&L) is
        represented as a separate AccountOverview entry.  All values are
        converted from USD to the configured base currency.

        Returns:
            List of AccountOverview objects with current account metrics
        """
        self.logger.debug("Getting Alpaca account overview")
        try:
            account = self.alpaca_client.get_account()
            now = timezone.now()

            equity = self._to_base(float(account.equity))
            cash = self._to_base(float(account.cash))
            buying_power = self._to_base(float(account.buying_power))
            last_equity = (
                self._to_base(float(account.last_equity))
                if hasattr(account, "last_equity") and account.last_equity
                else 0.0
            )
            daily_pl = equity - last_equity

            return [
                AccountOverview(
                    datetime=now,
                    value_datetime=now,
                    stock_name="Equity",
                    stock_symbol="equity",
                    description="Total account equity",
                    type="equity",
                    currency=self.base_currency,
                    change=equity,
                ),
                AccountOverview(
                    datetime=now,
                    value_datetime=now,
                    stock_name="Cash",
                    stock_symbol="cash",
                    description="Available cash balance",
                    type="cash",
                    currency=self.base_currency,
                    change=cash,
                ),
                AccountOverview(
                    datetime=now,
                    value_datetime=now,
                    stock_name="Buying Power",
                    stock_symbol="buying_power",
                    description="Available buying power",
                    type="buying_power",
                    currency=self.base_currency,
                    change=buying_power,
                ),
                AccountOverview(
                    datetime=now,
                    value_datetime=now,
                    stock_name="Daily P&L",
                    stock_symbol="daily_pl",
                    description="Profit and loss today",
                    type="daily_pl",
                    currency=self.base_currency,
                    change=daily_pl,
                ),
            ]
        except Exception as e:
            self.logger.error(f"Failed to fetch Alpaca account overview: {e}")
            return []
