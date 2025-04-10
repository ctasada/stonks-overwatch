import json
import pathlib

from stonks_overwatch.repositories.yfinance.models import YFinanceStockSplits, YFinanceTickerInfo
from stonks_overwatch.repositories.yfinance.yfinance_repository import YFinanceRepository

import pytest
from django.test import TestCase

@pytest.mark.django_db
class TestYFinanceRepository(TestCase):
    def setUp(self):
        self.fixture_ticker_info_repository()
        self.fixture_stock_split_repository()

    def fixture_ticker_info_repository(self):
        data_file = pathlib.Path("tests/resources/stonks_overwatch/repositories/y_finance/tickers_info_data.json")

        with open(data_file, "r") as file:
            data = json.load(file)

        self.created_objects = {}
        for key, value in data.items():
            # Create and save the Ticker Info objects
            obj = YFinanceTickerInfo.objects.create(
                symbol=key,
                data=value
            )
            self.created_objects[key] = obj


    def fixture_stock_split_repository(self):
        data_file = pathlib.Path("tests/resources/stonks_overwatch/repositories/y_finance/stocks_split_data.json")

        with open(data_file, "r") as file:
            data = json.load(file)

        self.created_objects = {}
        for key, value in data.items():
            # Create and save the Ticker Info objects
            obj = YFinanceStockSplits.objects.create(
                symbol=key,
                data=value
            )
            self.created_objects[key] = obj

    def tearDown(self):
        # Clean up the created objects
        for obj in self.created_objects.values():
            obj.delete()

    def test_get_known_symbol(self):
        info = YFinanceRepository.get_ticker_info("AAPL")

        assert info is not None
        print(info)
        assert info['industry'] == "Consumer Electronics"
        assert info['currency'] == "USD"
        assert info['symbol'] == "AAPL"
        assert info['country'] == "United States"

    def test_get_unknown_symbol(self):
        info = YFinanceRepository.get_ticker_info("XXX")

        assert info is None

    def test_unknown_stock_split(self):
        splits = YFinanceRepository.get_stock_splits("XXX")

        assert splits is None

    def test_symbol_without_splits(self):
        splits = YFinanceRepository.get_stock_splits("PLTR")

        assert splits is not None
        assert splits == []

    def test_symbol_with_splits(self):

        splits = YFinanceRepository.get_stock_splits("AAPL")
        assert splits is not None
        assert len(splits) == 5
        assert splits[3]['split_ratio'] == 7.0
        assert splits[4]['split_ratio'] == 4.0
