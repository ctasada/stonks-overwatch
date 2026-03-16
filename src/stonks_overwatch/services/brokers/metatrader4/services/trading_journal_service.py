from typing import List, Optional

from django.utils import timezone

from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.core.interfaces.trading_journal_service import TradingJournalServiceInterface
from stonks_overwatch.services.brokers.metatrader4.repositories.metatrader4_repository import Metatrader4Repository
from stonks_overwatch.services.models import AccountSummary, Trade
from stonks_overwatch.utils.core.logger import StonksLogger


class TradingJournalService(BaseService, TradingJournalServiceInterface):
    """
    MetaTrader4 Trading Journal Service.

    This service manages trading journal entries for MetaTrader4.
    """

    def __init__(self, config=None):
        super().__init__(config)
        self.logger = StonksLogger.get_logger(__name__, "[METATRADER4|TRADING_JOURNAL]")
        self.repository = Metatrader4Repository()
        # Cache only the currency string — the ORM summary row is fetched fresh per request.
        self.currency = self.repository.get_account_currency()
        # Instantiate once; building the converter constructs currency maps.
        from stonks_overwatch.services.brokers.degiro.services.currency_service import CurrencyConverterService

        self._currency_converter = CurrencyConverterService()

    def get_closed_trades(self) -> List[Trade]:
        """
        Retrieves all trades for MetaTrader4.

        Returns:
            List[Trade]: List of trades sorted by date (newest first)
        """
        self.logger.debug("Fetching closed trades")

        closed_trades = self.repository.get_closed_trades()
        base_currency = getattr(self.config, "base_currency", "EUR")

        transactions = []

        for trade in closed_trades:
            original_profit = float(trade.profit)
            original_currency = self.currency

            # Convert to base currency
            profit_base = self._currency_converter.convert(
                amount=original_profit,
                currency=original_currency,
                new_currency=base_currency,
                fx_date=trade.close_time.date(),
            )

            transactions.append(
                Trade(
                    name=trade.item,
                    datetime=trade.close_time,
                    profit=profit_base,
                    currency=base_currency,
                    original_profit=original_profit,
                    original_currency=original_currency,
                )
            )

        return transactions

    def get_account_summary(self) -> Optional[AccountSummary]:
        """
        Retrieve the latest account summary from MT4, with monetary values converted to base currency.

        Returns:
            AccountSummary with balance, unrealized P/L, equity, and margin in base currency, or None if no data
        """
        summary = self.repository.get_latest_summary()
        if not summary:
            return None

        base_currency = getattr(self.config, "base_currency", "EUR")
        today = timezone.now().date()

        def convert(amount: float) -> float:
            return self._currency_converter.convert(
                amount=amount,
                currency=self.currency,
                new_currency=base_currency,
                fx_date=today,
            )

        return AccountSummary(
            balance=convert(float(summary.balance or 0)),
            unrealized_pl=convert(float(summary.floating_pl or 0)),
            equity=convert(float(summary.equity or 0)),
            margin=convert(float(summary.margin or 0)),
            currency=base_currency,
        )
