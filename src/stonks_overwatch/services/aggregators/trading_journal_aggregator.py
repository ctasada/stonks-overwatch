from typing import List, Optional

from django.utils import timezone

from stonks_overwatch.core.aggregators.base_aggregator import BaseAggregator
from stonks_overwatch.core.exceptions import DataAggregationException
from stonks_overwatch.core.service_types import ServiceType
from stonks_overwatch.services.models import AccountSummary, PortfolioId, Trade


class TradingJournalAggregatorService(BaseAggregator):
    """
    Aggregator service for trading journal entries.

    This service aggregates trading journal entries from all enabled brokers
    and provides methods for managing and analyzing trading journal data.
    """

    def __init__(self):
        super().__init__(ServiceType.TRADING_JOURNAL)

    def get_closed_trades(self, selected_portfolio: PortfolioId) -> List[Trade]:
        """
        Get all trading journal entries from enabled brokers.

        Args:
            selected_portfolio: The selected portfolio to get entries for

        Returns:
            List of trading journal entries sorted by date (newest first)
        """
        # Collect entries from all brokers without sorting first to avoid timezone mixing
        combined_data = self._collect_and_merge_lists(selected_portfolio, "get_closed_trades")

        # Normalize all datetimes to be timezone-aware before sorting
        # This handles the case where different brokers return different timezone formats
        for entry in combined_data:
            if entry.datetime:
                if entry.datetime.tzinfo is None:
                    # Make timezone-naive datetimes timezone-aware using Django's default timezone
                    entry.datetime = timezone.make_aware(entry.datetime)

        # Now sort with normalized timezone-aware datetimes
        return sorted(combined_data, key=lambda x: x.datetime, reverse=True)

    def get_account_summary(self, selected_portfolio: PortfolioId) -> Optional[AccountSummary]:
        """
        Get an aggregated account summary across all enabled brokers that support it.

        Numeric fields (balance, unrealized P/L, equity, margin) are summed across brokers.
        The currency of the first available summary is used.

        Args:
            selected_portfolio: The selected portfolio to get the summary for

        Returns:
            Aggregated AccountSummary, or None if no broker provides summary data
        """
        try:
            broker_data = self._collect_broker_data(selected_portfolio, "get_account_summary")
        except DataAggregationException:
            return None

        summaries = [s for s in broker_data.values() if isinstance(s, AccountSummary)]
        if not summaries:
            return None

        return AccountSummary(
            balance=sum(s.balance for s in summaries),
            unrealized_pl=sum(s.unrealized_pl for s in summaries),
            equity=sum(s.equity for s in summaries),
            margin=sum(s.margin for s in summaries),
            currency=summaries[0].currency,
        )

    def aggregate_data(self, selected_portfolio: PortfolioId) -> List[Trade]:
        """
        Aggregate trading journal data from all enabled brokers.

        This is the main aggregation method required by BaseAggregator.

        Args:
            selected_portfolio: The selected portfolio to aggregate data for

        Returns:
            List of aggregated trading journal entries
        """
        return self.get_closed_trades(selected_portfolio)
