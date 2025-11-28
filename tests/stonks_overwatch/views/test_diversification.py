from stonks_overwatch.services.aggregators.portfolio_aggregator import PortfolioAggregatorService
from stonks_overwatch.utils.domain.constants import ProductType
from stonks_overwatch.views.diversification import Diversification

import pytest


class DummyPortfolioEntry:
    def __init__(self, name, symbol, value, product_type, product_type_share, is_open=True):
        self._name = name
        self.symbol = symbol
        self.value = value
        self.product_type = product_type
        self.product_type_share = product_type_share
        self.is_open = is_open
        if product_type_share is not None:
            self.formatted_product_type_share = f"{product_type_share:.2%}"
        else:
            self.formatted_product_type_share = "N/A"
        self.base_currency_value = value

    def formatted_name(self):
        return self._name

    def formatted_base_currency_value(self):
        return f"{self.value:.2f}"


def test_get_positions_etf():
    # Create dummy ETF and STOCK entries
    entries = [
        DummyPortfolioEntry("ETF1", "ETF1", 1000, ProductType.ETF, 0.6),
        DummyPortfolioEntry("ETF2", "ETF2", 500, ProductType.ETF, 0.3),
        DummyPortfolioEntry("ETF3", "ETF3", 200, ProductType.ETF, 0.1),
        DummyPortfolioEntry("STOCK1", "STOCK1", 100, ProductType.STOCK, 0.05),
    ]
    # Only ETF entries should be included
    result = Diversification._get_positions(entries, ProductType.ETF)
    table = result["table"]
    # Should be sorted by product_type_share descending
    sizes = [row["size"] for row in table]
    assert sizes == sorted(sizes, reverse=True)
    # Only ETF entries should be present
    assert all(row["product_type"] == "ETF" for row in table)
    # Chart labels and values match table order
    assert result["chart"]["labels"] == [row["name"] for row in table]
    # Compare chart values to the expected ETF base_currency_value values, sorted by product_type_share descending
    etf_entries = [e for e in entries if e.product_type == ProductType.ETF]
    etf_entries_sorted = sorted(etf_entries, key=lambda e: e.product_type_share, reverse=True)
    expected_values = [e.base_currency_value for e in etf_entries_sorted]
    assert result["chart"]["values"] == expected_values


def test_get_positions_stock():
    entries = [
        DummyPortfolioEntry("STOCK1", "STOCK1", 100, ProductType.STOCK, 0.5),
        DummyPortfolioEntry("STOCK2", "STOCK2", 200, ProductType.STOCK, 0.3),
        DummyPortfolioEntry("ETF1", "ETF1", 300, ProductType.ETF, 0.2),
    ]
    result = Diversification._get_positions(entries, ProductType.STOCK)
    table = result["table"]
    # Should be sorted by product_type_share descending
    sizes = [row["size"] for row in table]
    assert sizes == sorted(sizes, reverse=True)
    # Only STOCK entries should be present
    assert all(row["product_type"] == "STOCK" for row in table)
    # Chart labels and values match table order
    assert result["chart"]["labels"] == [row["name"] for row in table]
    stock_entries = [e for e in entries if e.product_type == ProductType.STOCK]
    stock_entries_sorted = sorted(stock_entries, key=lambda e: e.product_type_share, reverse=True)
    expected_values = [e.base_currency_value for e in stock_entries_sorted]
    assert result["chart"]["values"] == expected_values


def test_get_positions_empty_portfolio():
    result = Diversification._get_positions([], ProductType.STOCK)
    assert result["table"] == []
    assert result["chart"]["labels"] == []
    assert result["chart"]["values"] == []


def test_get_positions_all_closed():
    entries = [
        DummyPortfolioEntry("STOCK1", "STOCK1", 100, ProductType.STOCK, 0.5, is_open=False),
        DummyPortfolioEntry("ETF1", "ETF1", 200, ProductType.ETF, 0.5, is_open=False),
    ]
    result = Diversification._get_positions(entries, ProductType.STOCK)
    assert result["table"] == []
    assert result["chart"]["labels"] == []
    assert result["chart"]["values"] == []


def test_calculate_product_type_shares_single_group():
    # All entries are STOCK, values: 100, 200, 700
    entries = [
        DummyPortfolioEntry("A", "A", 100, ProductType.STOCK, None),
        DummyPortfolioEntry("B", "B", 200, ProductType.STOCK, None),
        DummyPortfolioEntry("C", "C", 700, ProductType.STOCK, None),
    ]
    for e in entries:
        e.product_type_share = None
        e.formatted_product_type_share = "N/A"
    PortfolioAggregatorService()._calculate_product_type_shares(entries)
    total = sum(e.value for e in entries)
    for e in entries:
        assert e.product_type_share == pytest.approx(e.value / total)
        e.formatted_product_type_share = f"{e.product_type_share:.2%}"


def test_calculate_product_type_shares_multiple_groups():
    # 2 STOCK, 2 ETF, 1 UNKNOWN
    entries = [
        DummyPortfolioEntry("S1", "S1", 100, ProductType.STOCK, None),
        DummyPortfolioEntry("S2", "S2", 300, ProductType.STOCK, None),
        DummyPortfolioEntry("E1", "E1", 200, ProductType.ETF, None),
        DummyPortfolioEntry("E2", "E2", 800, ProductType.ETF, None),
        DummyPortfolioEntry("U1", "U1", 500, ProductType.UNKNOWN, None),
    ]
    for e in entries:
        e.product_type_share = None
        e.formatted_product_type_share = "N/A"
    PortfolioAggregatorService()._calculate_product_type_shares(entries)
    stock_total = 100 + 300
    etf_total = 200 + 800
    for e in entries:
        if e.product_type == ProductType.STOCK:
            assert e.product_type_share == pytest.approx(e.value / stock_total)
        elif e.product_type == ProductType.ETF:
            assert e.product_type_share == pytest.approx(e.value / etf_total)
        elif e.product_type == ProductType.UNKNOWN:
            assert e.product_type_share == 0.0
        e.formatted_product_type_share = f"{e.product_type_share:.2%}"
