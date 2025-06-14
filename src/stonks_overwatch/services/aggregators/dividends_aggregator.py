from typing import List

from stonks_overwatch.core.aggregators.base_aggregator import BaseAggregator
from stonks_overwatch.core.factories.broker_registry import ServiceType
from stonks_overwatch.services.models import Dividend, PortfolioId


class DividendsAggregatorService(BaseAggregator):
    def __init__(self):
        super().__init__(ServiceType.DIVIDEND)

    def get_dividends(self, selected_portfolio: PortfolioId) -> List[Dividend]:
        # Use the new helper method to collect and sort dividend data
        return self._collect_and_sort(selected_portfolio, "get_dividends", sort_key=lambda k: k.payment_date)

    def aggregate_data(self, selected_portfolio: PortfolioId, **kwargs) -> List[Dividend]:
        """
        Aggregate dividend data from all enabled brokers.

        This is the main aggregation method required by BaseAggregator.
        """
        return self.get_dividends(selected_portfolio)
