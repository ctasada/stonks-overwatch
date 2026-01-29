from typing import List

from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.core.interfaces.trading_journal_service import TradingJournalServiceInterface
from stonks_overwatch.services.brokers.metatrader4.repositories.metatrader4_repository import Metatrader4Repository
from stonks_overwatch.services.models import Trade
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
        self.currency = self.repository.get_account_currency()

    def get_closed_trades(self) -> List[Trade]:
        """
        Retrieves all trades for MetaTrader4.

        Returns:
            List[Trade]: List of trades sorted by date (newest first)
        """
        from stonks_overwatch.services.brokers.degiro.services.currency_service import CurrencyConverterService

        self.logger.debug("Fetching closed trades")

        closed_trades = self.repository.get_closed_trades()
        base_currency = getattr(self.config, "base_currency", "EUR")
        currency_converter = CurrencyConverterService()

        transactions = []

        for trade in closed_trades:
            original_profit = float(trade.profit)
            original_currency = self.currency

            # Convert to base currency
            profit_base = currency_converter.convert(
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
