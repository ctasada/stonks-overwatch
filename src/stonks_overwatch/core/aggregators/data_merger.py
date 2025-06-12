"""
Data merger utilities for combining broker data.

This module provides utilities for merging specific data types from different
brokers, such as portfolio entries, historical values, and other financial data.
"""

from typing import Dict, List

from stonks_overwatch.services.models import DailyValue, PortfolioEntry, TotalPortfolio
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.domain.constants import ProductType

class DataMerger:
    """
    Utility class for merging financial data from multiple broker sources.

    This class provides static methods for merging different types of financial
    data while handling edge cases and maintaining data integrity.
    """

    logger = StonksLogger.get_logger("stonks_overwatch.data_merger", "[DATA_MERGER]")

    @staticmethod
    def merge_portfolio_entries(portfolio_entries: List[PortfolioEntry]) -> List[PortfolioEntry]:
        """
        Merge portfolio entries from multiple brokers, combining entries for the same symbol.

        Args:
            portfolio_entries: List of portfolio entries from different brokers

        Returns:
            List of merged portfolio entries
        """
        merged = {}

        for entry in portfolio_entries:
            symbol = entry.symbol
            if symbol not in merged:
                merged[symbol] = entry
            else:
                if entry.product_type == ProductType.CASH:
                    # For cash entries, simply add the values
                    merged[symbol].value += entry.value
                    merged[symbol].base_currency_value += entry.base_currency_value
                else:
                    # For other assets, merge using detailed logic
                    merged[symbol] = DataMerger._merge_single_portfolio_entry(merged[symbol], entry)

        return list(merged.values())

    @staticmethod
    def _merge_single_portfolio_entry(entry1: PortfolioEntry, entry2: PortfolioEntry) -> PortfolioEntry:
        """
        Merge two portfolio entries for the same symbol.

        Args:
            entry1: First portfolio entry
            entry2: Second portfolio entry

        Returns:
            Merged portfolio entry

        Raises:
            ValueError: If entries have different symbols
        """
        if entry1.symbol != entry2.symbol:
            raise ValueError(f"Cannot merge entries with different symbols: {entry1.symbol} vs {entry2.symbol}")

        # Create merged entry with combined values
        merged_entry = PortfolioEntry(
            name=entry1.name or entry2.name,
            symbol=entry1.symbol,
            isin=entry1.isin or entry2.isin,
            sector=entry1.sector or entry2.sector,
            industry=entry1.industry if entry1.industry != 'Unknown' else entry2.industry,
            category=entry1.category or entry2.category,
            exchange=entry1.exchange or entry2.exchange,
            country=entry1.country or entry2.country,
            product_type=entry1.product_type,
            shares=entry1.shares + entry2.shares,
            product_currency=entry1.product_currency,
            price=entry1.price,  # Use price from first entry (they should be the same)
            base_currency_price=entry1.base_currency_price,
            base_currency=entry1.base_currency,
            value=entry1.value + entry2.value,
            base_currency_value=entry1.base_currency_value + entry2.base_currency_value,
            is_open=entry1.is_open or entry2.is_open,  # Open if either is open
            unrealized_gain=(entry1.unrealized_gain or 0) + (entry2.unrealized_gain or 0),
            realized_gain=(entry1.realized_gain or 0) + (entry2.realized_gain or 0),
            total_costs=(entry1.total_costs or 0) + (entry2.total_costs or 0),
        )

        # Handle break-even prices based on which positions are open
        if entry1.is_open and not entry2.is_open:
            merged_entry.break_even_price = entry1.break_even_price
            merged_entry.base_currency_break_even_price = entry1.base_currency_break_even_price
        elif not entry1.is_open and entry2.is_open:
            merged_entry.break_even_price = entry2.break_even_price
            merged_entry.base_currency_break_even_price = entry2.base_currency_break_even_price
        elif entry1.is_open and entry2.is_open:
            # Both are open - calculate weighted average break-even price
            total_shares = entry1.shares + entry2.shares
            if total_shares > 0:
                weighted_break_even = (
                    (entry1.break_even_price or 0) * entry1.shares +
                    (entry2.break_even_price or 0) * entry2.shares
                ) / total_shares
                weighted_base_break_even = (
                    (entry1.base_currency_break_even_price or 0) * entry1.shares +
                    (entry2.base_currency_break_even_price or 0) * entry2.shares
                ) / total_shares

                merged_entry.break_even_price = weighted_break_even
                merged_entry.base_currency_break_even_price = weighted_base_break_even

        return merged_entry

    @staticmethod
    def merge_historical_values(historical_values: List[DailyValue]) -> List[DailyValue]:
        """
        Merge historical values from multiple brokers by date.

        Args:
            historical_values: List of daily values from different brokers

        Returns:
            List of merged daily values sorted by date
        """
        merged = {}

        for entry in historical_values:
            date = entry["x"]
            value = float(entry["y"])

            if date not in merged:
                merged[date] = 0.0
            merged[date] += value

        # Convert back to DailyValue objects and sort by date
        merged_values = [
            DailyValue(x=date, y=value)
            for date, value in sorted(merged.items())
        ]

        return merged_values

    @staticmethod
    def merge_total_portfolios(total_portfolios: List[TotalPortfolio]) -> TotalPortfolio:
        """
        Merge total portfolio summaries from multiple brokers.

        Args:
            total_portfolios: List of total portfolio summaries

        Returns:
            Merged total portfolio summary
        """
        if not total_portfolios:
            raise ValueError("Cannot merge empty list of total portfolios")

        # Use the base currency from the first portfolio
        base_currency = total_portfolios[0].base_currency

        # Sum all the values
        total_pl = sum(portfolio.total_pl for portfolio in total_portfolios)
        total_cash = sum(portfolio.total_cash for portfolio in total_portfolios)
        current_value = sum(portfolio.current_value for portfolio in total_portfolios)
        total_deposit_withdrawal = sum(portfolio.total_deposit_withdrawal for portfolio in total_portfolios)

        # Calculate combined ROI
        roi = 0.0
        if total_deposit_withdrawal > 0:
            roi = (current_value / total_deposit_withdrawal - 1) * 100

        return TotalPortfolio(
            base_currency=base_currency,
            total_pl=total_pl,
            total_cash=total_cash,
            current_value=current_value,
            total_roi=roi,
            total_deposit_withdrawal=total_deposit_withdrawal,
        )

    @staticmethod
    def merge_dictionaries_by_sum(dictionaries: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Merge dictionaries by summing values for matching keys.

        Args:
            dictionaries: List of dictionaries with string keys and numeric values

        Returns:
            Merged dictionary with summed values
        """
        merged = {}

        for dictionary in dictionaries:
            for key, value in dictionary.items():
                if key not in merged:
                    merged[key] = 0.0
                merged[key] += float(value)

        return merged

    @staticmethod
    def merge_lists_with_sort(data_lists: List[List], sort_key=None, reverse: bool = False) -> List:
        """
        Merge multiple lists and sort the result.

        Args:
            data_lists: List of lists to merge
            sort_key: Function to use for sorting (optional)
            reverse: Whether to sort in reverse order

        Returns:
            Merged and sorted list
        """
        merged = []
        for data_list in data_lists:
            if data_list:
                merged.extend(data_list)

        if sort_key:
            return sorted(merged, key=sort_key, reverse=reverse)
        else:
            return sorted(merged, reverse=reverse)
