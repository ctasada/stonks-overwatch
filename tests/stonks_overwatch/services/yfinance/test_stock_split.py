from datetime import datetime

from stonks_overwatch.services.brokers.yfinance.client.yfinance_client import StockSplit

import pytest

@pytest.fixture
def sample_date():
    return datetime(2024, 3, 15, 12, 0)

@pytest.fixture
def sample_stock_split(sample_date):
    return StockSplit(date=sample_date, split_ratio=2.0)

def test_stock_split_initialization(sample_date):
    stock_split = StockSplit(date=sample_date, split_ratio=2.0)
    assert stock_split.date == sample_date
    assert stock_split.split_ratio == 2.0

def test_stock_split_to_dict(sample_stock_split):
    expected_dict = {
        "date": "2024-03-15T12:00:00",
        "split_ratio": 2.0
    }
    assert sample_stock_split.to_dict() == expected_dict

def test_stock_split_from_dict(sample_date):
    sample_dict = {
        "date": "2024-03-15T12:00:00",
        "split_ratio": 2.0
    }
    stock_split = StockSplit.from_dict(sample_dict)
    assert stock_split.date == sample_date
    assert stock_split.split_ratio == 2.0
