from typing import List

from stonks_overwatch.core.aggregators.base_aggregator import BaseAggregator
from stonks_overwatch.core.service_types import ServiceType
from stonks_overwatch.services.models import PortfolioId, Trade


class TradesAggregatorService(BaseAggregator):
    def __init__(self):
        super().__init__(ServiceType.TRADE)

    def get_trades(self, selected_portfolio: PortfolioId) -> List[Trade]:
        # Use the new helper method to collect and sort trade data
        return self._collect_and_sort(
            selected_portfolio,
            "get_trades",
            sort_key=lambda k: (k.date, k.time, 1 if k.buy_sell == "S" else 0),
            reverse=True,
        )

    def aggregate_data(self, selected_portfolio: PortfolioId) -> List[Trade]:
        """
        Aggregate trades data from all enabled brokers.

        This is the main aggregation method required by BaseAggregator.
        """
        return self.get_trades(selected_portfolio)
