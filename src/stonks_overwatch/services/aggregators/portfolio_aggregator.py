from typing import List

from stonks_overwatch.config.config import Config
from stonks_overwatch.core.aggregators.base_aggregator import BaseAggregator
from stonks_overwatch.core.aggregators.data_merger import DataMerger
from stonks_overwatch.core.factories.broker_registry import ServiceType
from stonks_overwatch.services.brokers.yfinance.services.market_data_service import YFinance
from stonks_overwatch.services.models import DailyValue, PortfolioEntry, PortfolioId, TotalPortfolio
from stonks_overwatch.utils.domain.constants import ProductType, Sector

class PortfolioAggregatorService(BaseAggregator):

    def __init__(self):
        super().__init__(ServiceType.PORTFOLIO)
        self.yfinance = YFinance()

    def get_portfolio(self, selected_portfolio: PortfolioId) -> List[PortfolioEntry]:
        self._logger.debug("Get Portfolio")

        # Use the new helper method to collect and merge portfolio data
        portfolio = self._collect_and_merge_lists(
            selected_portfolio,
            "get_portfolio",
            merger_func=DataMerger.merge_portfolio_entries
        )

        # Apply business-specific enrichment logic
        portfolio_total_value = sum([entry.value for entry in portfolio])

        # Calculate Stock Portfolio Size & add missing information
        for entry in portfolio:
            size = entry.value / portfolio_total_value if portfolio_total_value > 0 else 0.0
            entry.portfolio_size = size

            # If some data is missing, we try to get it from yfinance
            if not entry.country and entry.product_type in [ProductType.STOCK, ProductType.ETF]:
                entry.country = self.yfinance.get_country(entry.symbol)

            if entry.product_type == ProductType.CASH:
                entry.sector = Sector.CASH
            elif entry.product_type == ProductType.CRYPTO:
                entry.sector = Sector.CRYPTO
            elif entry.product_type == ProductType.ETF:
                entry.sector = Sector.ETF

            if ((entry.sector == Sector.UNKNOWN or entry.industry == 'Unknown')
                    and entry.product_type in [ProductType.STOCK]):
                sector, industry = self.yfinance.get_sector_industry(entry.symbol)
                if entry.sector == Sector.UNKNOWN:
                    entry.sector = sector
                if entry.industry == 'Unknown':
                    entry.industry = industry

            if entry.sector == Sector.UNKNOWN:
                self._logger.warning(f"Warning: Sector for {entry.symbol} is UNKNOWN.")

        return sorted(portfolio, key=lambda k: k.symbol)

    def get_portfolio_total(self, selected_portfolio: PortfolioId) -> TotalPortfolio:
        self._logger.debug("Get Portfolio Total")

        # Use the new helper method to collect and merge portfolio totals
        merged_total = self._collect_and_merge_objects(
            selected_portfolio,
            "get_portfolio_total",
            expected_type=TotalPortfolio,
            merger_func=DataMerger.merge_total_portfolios,
            portfolio=None
        )

        # If we got a merged result, return it; otherwise return empty portfolio
        if isinstance(merged_total, TotalPortfolio):
            return merged_total
        else:
            # Return empty portfolio if no data
            base_currency = Config.default().base_currency
            return TotalPortfolio(
                base_currency=base_currency,
                total_pl=0.0,
                total_cash=0.0,
                current_value=0.0,
                total_roi=0.0,
                total_deposit_withdrawal=0.0,
            )

    def calculate_historical_value(self, selected_portfolio: PortfolioId) -> List[DailyValue]:
        self._logger.debug(f"Calculating historical value for {selected_portfolio}")

        # Use the new helper method to collect and merge historical data
        return self._collect_and_merge_lists(
            selected_portfolio,
            "calculate_historical_value",
            merger_func=DataMerger.merge_historical_values
        )

    def aggregate_data(self, selected_portfolio: PortfolioId, **kwargs) -> List[PortfolioEntry]:
        """
        Aggregate portfolio data from all enabled brokers.

        This is the main aggregation method required by BaseAggregator.
        It calls get_portfolio internally.
        """
        return self.get_portfolio(selected_portfolio)
