from typing import List

from stonks_overwatch.core.aggregators.base_aggregator import BaseAggregator
from stonks_overwatch.core.service_types import ServiceType
from stonks_overwatch.services.models import AccountOverview, PortfolioId


class AccountOverviewAggregatorService(BaseAggregator):
    def __init__(self):
        super().__init__(ServiceType.ACCOUNT)

    def get_account_overview(self, selected_portfolio: PortfolioId) -> List[AccountOverview]:
        # Use the new helper method to collect and sort account overview data
        return self._collect_and_sort(
            selected_portfolio, "get_account_overview", sort_key=lambda k: k.datetime, reverse=True
        )

    def aggregate_data(self, selected_portfolio: PortfolioId) -> List[AccountOverview]:
        """
        Aggregate account overview data from all enabled brokers.

        This is the main aggregation method required by BaseAggregator.
        """
        return self.get_account_overview(selected_portfolio)
