"""
Tests for DataMerger.

This module contains comprehensive tests for the data merger utilities,
covering portfolio entry merging, historical values, total portfolios, and utility methods.
"""

from stonks_overwatch.core.aggregators.data_merger import DataMerger
from stonks_overwatch.services.models import DailyValue, PortfolioEntry, TotalPortfolio
from stonks_overwatch.utils.domain.constants import ProductType

import pytest

class TestDataMerger:
    """Test cases for DataMerger."""

    def test_merge_portfolio_entries_different_symbols(self):
        """Test merging portfolio entries with different symbols."""
        entry1 = PortfolioEntry(
            symbol="AAPL",
            name="Apple Inc.",
            shares=10.0,
            price=150.0,
            value=1500.0,
            product_type=ProductType.STOCK
        )

        entry2 = PortfolioEntry(
            symbol="GOOGL",
            name="Alphabet Inc.",
            shares=5.0,
            price=2800.0,
            value=14000.0,
            product_type=ProductType.STOCK
        )

        # Merge entries
        result = DataMerger.merge_portfolio_entries([entry1, entry2])

        # Should have two separate entries
        assert len(result) == 2
        symbols = [entry.symbol for entry in result]
        assert "AAPL" in symbols
        assert "GOOGL" in symbols

    def test_merge_portfolio_entries_same_symbol(self):
        """Test merging portfolio entries with the same symbol."""
        entry1 = PortfolioEntry(
            symbol="AAPL",
            name="Apple Inc.",
            shares=10.0,
            price=150.0,
            value=1500.0,
            base_currency_value=1500.0,
            product_type=ProductType.STOCK,
            is_open=True,
            unrealized_gain=100.0,
            realized_gain=50.0,
            total_costs=1400.0
        )

        entry2 = PortfolioEntry(
            symbol="AAPL",
            name="Apple Inc.",
            shares=5.0,
            price=150.0,
            value=750.0,
            base_currency_value=750.0,
            product_type=ProductType.STOCK,
            is_open=True,
            unrealized_gain=50.0,
            realized_gain=25.0,
            total_costs=700.0
        )

        # Merge entries
        result = DataMerger.merge_portfolio_entries([entry1, entry2])

        # Should have one merged entry
        assert len(result) == 1
        merged = result[0]

        # Verify merged values
        assert merged.symbol == "AAPL"
        assert merged.shares == 15.0  # 10 + 5
        assert merged.value == 2250.0  # 1500 + 750
        assert merged.base_currency_value == 2250.0  # 1500 + 750
        assert merged.unrealized_gain == 150.0  # 100 + 50
        assert merged.realized_gain == 75.0  # 50 + 25
        assert merged.total_costs == 2100.0  # 1400 + 700

    def test_merge_portfolio_entries_cash_type(self):
        """Test merging cash portfolio entries."""
        cash1 = PortfolioEntry(
            symbol="EUR",
            name="Cash Balance EUR",
            value=1000.0,
            base_currency_value=1000.0,
            product_type=ProductType.CASH
        )

        cash2 = PortfolioEntry(
            symbol="EUR",
            name="Cash Balance EUR",
            value=500.0,
            base_currency_value=500.0,
            product_type=ProductType.CASH
        )

        # Merge entries
        result = DataMerger.merge_portfolio_entries([cash1, cash2])

        # Should have one merged cash entry
        assert len(result) == 1
        merged = result[0]

        # Verify merged cash values
        assert merged.symbol == "EUR"
        assert merged.value == 1500.0  # 1000 + 500
        assert merged.base_currency_value == 1500.0  # 1000 + 500

    def test_merge_single_portfolio_entry_different_symbols_raises_error(self):
        """Test that merging entries with different symbols raises an error."""
        entry1 = PortfolioEntry(symbol="AAPL", product_type=ProductType.STOCK)
        entry2 = PortfolioEntry(symbol="GOOGL", product_type=ProductType.STOCK)

        with pytest.raises(ValueError) as exc_info:
            DataMerger._merge_single_portfolio_entry(entry1, entry2)

        assert "Cannot merge entries with different symbols" in str(exc_info.value)

    def test_merge_single_portfolio_entry_break_even_prices(self):
        """Test break-even price calculation when merging entries."""
        # Both positions open - should calculate weighted average
        entry1 = PortfolioEntry(
            symbol="AAPL",
            shares=10.0,
            break_even_price=140.0,
            base_currency_break_even_price=140.0,
            is_open=True,
            product_type=ProductType.STOCK
        )

        entry2 = PortfolioEntry(
            symbol="AAPL",
            shares=5.0,
            break_even_price=160.0,
            base_currency_break_even_price=160.0,
            is_open=True,
            product_type=ProductType.STOCK
        )

        # Merge entries
        result = DataMerger._merge_single_portfolio_entry(entry1, entry2)

        # Verify weighted average: (140*10 + 160*5) / 15 = 146.67
        expected_break_even = (140.0 * 10.0 + 160.0 * 5.0) / 15.0
        assert abs(result.break_even_price - expected_break_even) < 0.01
        assert abs(result.base_currency_break_even_price - expected_break_even) < 0.01

    def test_merge_historical_values(self):
        """Test merging historical values by date."""
        values = [
            DailyValue(x="2023-01-01", y=1000.0),
            DailyValue(x="2023-01-02", y=1100.0),
            DailyValue(x="2023-01-01", y=500.0),  # Same date, should be summed
            DailyValue(x="2023-01-03", y=1200.0),
        ]

        # Merge values
        result = DataMerger.merge_historical_values(values)

        # Should have 3 entries (2023-01-01 combined)
        assert len(result) == 3

        # Check that values are sorted by date
        dates = [entry["x"] for entry in result]
        assert dates == ["2023-01-01", "2023-01-02", "2023-01-03"]

        # Check that same-date values are summed
        jan_01_entry = next(entry for entry in result if entry["x"] == "2023-01-01")
        assert jan_01_entry["y"] == 1500.0  # 1000 + 500

    def test_merge_total_portfolios(self):
        """Test merging total portfolio summaries."""
        portfolio1 = TotalPortfolio(
            base_currency="EUR",
            total_pl=1000.0,
            total_cash=500.0,
            current_value=15000.0,
            total_roi=10.0,
            total_deposit_withdrawal=14000.0
        )

        portfolio2 = TotalPortfolio(
            base_currency="EUR",
            total_pl=500.0,
            total_cash=200.0,
            current_value=8000.0,
            total_roi=8.0,
            total_deposit_withdrawal=7500.0
        )

        # Merge portfolios
        result = DataMerger.merge_total_portfolios([portfolio1, portfolio2])

        # Verify merged values
        assert result.base_currency == "EUR"
        assert result.total_pl == 1500.0  # 1000 + 500
        assert result.total_cash == 700.0  # 500 + 200
        assert result.current_value == 23000.0  # 15000 + 8000
        assert result.total_deposit_withdrawal == 21500.0  # 14000 + 7500

        # ROI should be recalculated: (23000 / 21500 - 1) * 100
        expected_roi = (23000.0 / 21500.0 - 1) * 100
        assert abs(result.total_roi - expected_roi) < 0.01

    def test_merge_total_portfolios_empty_list_raises_error(self):
        """Test that merging empty list of portfolios raises an error."""
        with pytest.raises(ValueError) as exc_info:
            DataMerger.merge_total_portfolios([])

        assert "Cannot merge empty list of total portfolios" in str(exc_info.value)

    def test_merge_dictionaries_by_sum(self):
        """Test merging dictionaries by summing values."""
        dict1 = {"AAPL": 100.0, "GOOGL": 200.0, "MSFT": 150.0}
        dict2 = {"AAPL": 50.0, "TSLA": 300.0, "MSFT": 100.0}
        dict3 = {"GOOGL": 100.0, "AMZN": 250.0}

        # Merge dictionaries
        result = DataMerger.merge_dictionaries_by_sum([dict1, dict2, dict3])

        # Verify merged values
        assert result["AAPL"] == 150.0  # 100 + 50
        assert result["GOOGL"] == 300.0  # 200 + 100
        assert result["MSFT"] == 250.0  # 150 + 100
        assert result["TSLA"] == 300.0  # Only from dict2
        assert result["AMZN"] == 250.0  # Only from dict3

    def test_merge_lists_with_sort_no_sort_key(self):
        """Test merging and sorting lists without sort key."""
        list1 = [3, 1, 4]
        list2 = [2, 5]
        list3 = [6]

        # Merge and sort
        result = DataMerger.merge_lists_with_sort([list1, list2, list3])

        # Should be sorted in ascending order
        assert result == [1, 2, 3, 4, 5, 6]

    def test_merge_lists_with_sort_with_sort_key(self):
        """Test merging and sorting lists with custom sort key."""
        list1 = ["apple", "banana"]
        list2 = ["cat", "dog"]
        list3 = ["elephant"]

        # Merge and sort by length
        result = DataMerger.merge_lists_with_sort([list1, list2, list3], sort_key=len)

        # Should be sorted by string length
        assert result == ["cat", "dog", "apple", "banana", "elephant"]

    def test_merge_lists_with_sort_reverse(self):
        """Test merging and sorting lists in reverse order."""
        list1 = [1, 3]
        list2 = [2, 4]

        # Merge and sort in reverse
        result = DataMerger.merge_lists_with_sort([list1, list2], reverse=True)

        # Should be sorted in descending order
        assert result == [4, 3, 2, 1]

    def test_merge_lists_with_sort_empty_lists(self):
        """Test merging lists with some empty lists."""
        list1 = [1, 2]
        list2 = []
        list3 = [3, 4]

        # Filter out None before calling merge
        lists_to_merge = [lst for lst in [list1, list2, list3] if lst is not None]

        # Merge and sort
        result = DataMerger.merge_lists_with_sort(lists_to_merge)

        # Should merge non-empty lists and sort
        assert result == [1, 2, 3, 4]
