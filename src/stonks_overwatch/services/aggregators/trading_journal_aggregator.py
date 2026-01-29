from typing import List

from django.utils import timezone

from stonks_overwatch.core.aggregators.base_aggregator import BaseAggregator
from stonks_overwatch.core.service_types import ServiceType
from stonks_overwatch.services.models import PortfolioId, Trade


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
