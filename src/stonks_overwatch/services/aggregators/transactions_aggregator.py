from typing import List

from stonks_overwatch.core.aggregators.base_aggregator import BaseAggregator
from stonks_overwatch.core.service_types import ServiceType
from stonks_overwatch.services.models import PortfolioId, Transaction


class TransactionsAggregatorService(BaseAggregator):
    def __init__(self):
        super().__init__(ServiceType.TRANSACTION)

    def get_transactions(self, selected_portfolio: PortfolioId) -> List[Transaction]:
        # Use the new helper method to collect and sort transaction data
        return self._collect_and_sort(
            selected_portfolio,
            "get_transactions",
            sort_key=lambda k: (k.date, k.time, 1 if k.buy_sell == "S" else 0),
            reverse=True,
        )

    def aggregate_data(self, selected_portfolio: PortfolioId, **kwargs) -> List[Transaction]:
        """
        Aggregate transaction data from all enabled brokers.

        This is the main aggregation method required by BaseAggregator.
        """
        return self.get_transactions(selected_portfolio)
