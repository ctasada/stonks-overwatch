import json
import pathlib

from stonks_overwatch.repositories.yfinance.models import YFinanceStockSplits, YFinanceTickerInfo
from stonks_overwatch.repositories.yfinance.yfinance_repository import YFinanceRepository

import pytest
from django.test import TestCase

@pytest.mark.django_db
class TestYFinanceRepository(TestCase):
    """Tests for the YFinanceRepository class.

    Test data includes:
    - Apple Inc (AAPL) ticker info and stock splits
    - Palantir (PLTR) ticker info without splits
    """
    def setUp(self):
        """Set up test data for both ticker info and stock splits."""
        # Load ticker info data
        data_file = pathlib.Path("tests/resources/stonks_overwatch/repositories/y_finance/tickers_info_data.json")
        with open(data_file, "r") as file:
            data = json.load(file)

        self.ticker_info = {}
        for key, value in data.items():
            obj = YFinanceTickerInfo.objects.create(
                symbol=key,
                data=value
            )
            self.ticker_info[key] = obj

        # Load stock splits data
        data_file = pathlib.Path("tests/resources/stonks_overwatch/repositories/y_finance/stocks_split_data.json")
        with open(data_file, "r") as file:
            data = json.load(file)

        self.stock_splits = {}
        for key, value in data.items():
            obj = YFinanceStockSplits.objects.create(
                symbol=key,
                data=value
            )
            self.stock_splits[key] = obj

    def tearDown(self):
        """Clean up all test data."""
        # Clean up ticker info
        for obj in self.ticker_info.values():
            obj.delete()
        # Clean up stock splits
        for obj in self.stock_splits.values():
            obj.delete()

    def test_get_known_symbol(self):
        """Test retrieving ticker info for a known symbol."""
        info = YFinanceRepository.get_ticker_info("AAPL")
        self.assertIsNotNone(info)
        self.assertEqual(info['industry'], "Consumer Electronics")
        self.assertEqual(info['currency'], "USD")
        self.assertEqual(info['symbol'], "AAPL")
        self.assertEqual(info['country'], "United States")

    def test_get_unknown_symbol(self):
        """Test retrieving ticker info for an unknown symbol."""
        info = YFinanceRepository.get_ticker_info("XXX")
        self.assertIsNone(info)

    def test_unknown_stock_split(self):
        """Test retrieving stock splits for an unknown symbol."""
        splits = YFinanceRepository.get_stock_splits("XXX")
        self.assertIsNone(splits)

    def test_symbol_without_splits(self):
        """Test retrieving stock splits for a symbol without splits."""
        splits = YFinanceRepository.get_stock_splits("PLTR")
        self.assertIsNotNone(splits)
        self.assertEqual(len(splits), 0)

    def test_symbol_with_splits(self):
        """Test retrieving stock splits for a symbol with splits."""
        splits = YFinanceRepository.get_stock_splits("AAPL")
        self.assertIsNotNone(splits)
        self.assertEqual(len(splits), 5)
        self.assertEqual(splits[3]['split_ratio'], 7.0)
        self.assertEqual(splits[4]['split_ratio'], 4.0)
