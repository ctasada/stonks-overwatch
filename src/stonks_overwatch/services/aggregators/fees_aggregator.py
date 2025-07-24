from stonks_overwatch.core.aggregators.base_aggregator import BaseAggregator
from stonks_overwatch.core.factories.broker_registry import ServiceType
from stonks_overwatch.services.models import Fee, PortfolioId


class FeesAggregatorService(BaseAggregator):
    def __init__(self):
        super().__init__(ServiceType.FEE)

    def get_fees(self, selected_portfolio: PortfolioId) -> list[Fee]:
        # Use the new helper method to collect and sort fee data
        return self._collect_and_sort(selected_portfolio, "get_fees", sort_key=lambda k: (k.date, k.time), reverse=True)

    def aggregate_data(self, selected_portfolio: PortfolioId, **kwargs) -> list[Fee]:
        """
        Aggregate fee data from all enabled brokers.

        This is the main aggregation method required by BaseAggregator.
        """
        return self.get_fees(selected_portfolio)
