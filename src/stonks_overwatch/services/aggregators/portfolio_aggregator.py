from collections import defaultdict
from typing import List

from stonks_overwatch.core.aggregators.base_aggregator import BaseAggregator
from stonks_overwatch.core.aggregators.data_merger import DataMerger
from stonks_overwatch.core.service_types import ServiceType
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
            selected_portfolio, "get_portfolio", merger_func=DataMerger.merge_portfolio_entries
        )

        self._calculate_product_type_shares(portfolio)
        self._fill_missing_entry_info(portfolio)

        return sorted(portfolio, key=lambda k: k.symbol)

    def _calculate_product_type_shares(self, portfolio: List[PortfolioEntry]):
        group_map = defaultdict(list)
        for entry in portfolio:
            if entry.product_type != ProductType.UNKNOWN:
                group_map[entry.product_type].append(entry)
            else:
                entry.product_type_share = 0.0  # Explicitly set for UNKNOWN
        for entries in group_map.values():
            group_total = sum(e.value for e in entries)
            for e in entries:
                e.product_type_share = (e.value / group_total) if group_total > 0 else 0.0

    def _fill_missing_entry_info(self, portfolio: List[PortfolioEntry]):
        for entry in portfolio:
            self._assign_country(entry)
            self._assign_sector(entry)
            self._assign_industry(entry)
            self._warn_if_unknown_sector(entry)

    def _assign_country(self, entry: PortfolioEntry):
        if not entry.country and entry.product_type in [ProductType.STOCK, ProductType.ETF]:
            entry.country = self.yfinance.get_country(entry.symbol)

    def _assign_sector(self, entry: PortfolioEntry):
        if entry.product_type == ProductType.CASH:
            entry.sector = Sector.CASH
        elif entry.product_type == ProductType.CRYPTO:
            entry.sector = Sector.CRYPTO
        elif entry.product_type == ProductType.ETF:
            entry.sector = Sector.ETF
        elif entry.product_type == ProductType.STOCK and entry.sector == Sector.UNKNOWN:
            sector, _ = self.yfinance.get_sector_industry(entry.symbol)
            if sector != Sector.UNKNOWN:
                entry.sector = sector

    def _assign_industry(self, entry: PortfolioEntry):
        if entry.product_type == ProductType.STOCK and entry.industry == "Unknown":
            _, industry = self.yfinance.get_sector_industry(entry.symbol)
            if industry and industry != "Unknown":
                entry.industry = industry

    def _warn_if_unknown_sector(self, entry: PortfolioEntry):
        if entry.sector == Sector.UNKNOWN:
            self._logger.warning(f"Warning: Sector for {entry.symbol} is UNKNOWN.")

    def get_portfolio_total(self, selected_portfolio: PortfolioId) -> TotalPortfolio:
        self._logger.debug(f"Get Portfolio Total. Selected Portfolio: {selected_portfolio}")

        # Use the new helper method to collect and merge portfolio totals
        merged_total = self._collect_and_merge_objects(
            selected_portfolio,
            "get_portfolio_total",
            expected_type=TotalPortfolio,
            merger_func=DataMerger.merge_total_portfolios,
            portfolio=None,
        )

        # If we got a merged result, return it; otherwise return empty portfolio
        if isinstance(merged_total, TotalPortfolio):
            return merged_total
        else:
            # Return empty portfolio if no data
            base_currency = self.config.base_currency
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
            selected_portfolio, "calculate_historical_value", merger_func=DataMerger.merge_historical_values
        )

    def aggregate_data(self, selected_portfolio: PortfolioId) -> List[PortfolioEntry]:
        """
        Aggregate portfolio data from all enabled brokers.

        This is the main aggregation method required by BaseAggregator.
        It calls get_portfolio internally.
        """
        return self.get_portfolio(selected_portfolio)
