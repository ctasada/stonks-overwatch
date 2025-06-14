from datetime import datetime

from stonks_overwatch.services.brokers.yfinance.client.yfinance_client import StockSplit
from stonks_overwatch.services.brokers.yfinance.services.market_data_service import YFinance
from stonks_overwatch.services.models import Country
from stonks_overwatch.utils.domain.constants import Sector

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_yfinance_client():
    with patch("stonks_overwatch.services.brokers.yfinance.services.market_data_service.YFinanceClient") as mock:
        client_instance = MagicMock()
        mock.return_value = client_instance
        yield client_instance


@pytest.fixture
def mock_yfinance_repository():
    with patch("stonks_overwatch.services.brokers.yfinance.services.market_data_service.YFinanceRepository") as mock:
        repo_instance = MagicMock()
        mock.return_value = repo_instance
        yield repo_instance


@pytest.fixture
def yfinance_service(mock_yfinance_client, mock_yfinance_repository):
    service = YFinance()
    service.client = mock_yfinance_client
    service.repository = mock_yfinance_repository
    return service


def test_get_stock_splits_from_repository(yfinance_service, mock_yfinance_client, mock_yfinance_repository):
    """Test getting stock splits from a repository when data exists."""
    # Setup
    symbol = "AAPL"
    mock_splits = [
        {"date": "2024-03-15T12:00:00", "split_ratio": 2.0},
        {"date": "2020-08-31T12:00:00", "split_ratio": 4.0},
    ]
    mock_yfinance_repository.get_stock_splits.return_value = mock_splits

    # Execute
    result = yfinance_service.get_stock_splits(symbol)

    # Verify
    assert len(result) == 2
    assert isinstance(result[0], StockSplit)
    assert result[0].date == datetime.fromisoformat("2024-03-15T12:00:00")
    assert result[0].split_ratio == 2.0
    assert result[1].date == datetime.fromisoformat("2020-08-31T12:00:00")
    assert result[1].split_ratio == 4.0
    mock_yfinance_repository.get_stock_splits.assert_called_once_with(symbol)
    mock_yfinance_client.get_stock_splits.assert_not_called()


def test_get_stock_splits_from_client(yfinance_service, mock_yfinance_client, mock_yfinance_repository):
    """Test getting stock splits from a client when repository has no data."""
    # Setup
    symbol = "AAPL"
    mock_yfinance_repository.get_stock_splits.return_value = None
    mock_splits = [
        StockSplit(date=datetime(2024, 3, 15, 12, 0), split_ratio=2.0),
        StockSplit(date=datetime(2020, 8, 31, 12, 0), split_ratio=4.0),
    ]
    mock_yfinance_client.get_stock_splits.return_value = mock_splits

    # Execute
    result = yfinance_service.get_stock_splits(symbol)

    # Verify
    assert len(result) == 2
    assert isinstance(result[0], StockSplit)
    assert result[0].date == datetime(2024, 3, 15, 12, 0)
    assert result[0].split_ratio == 2.0
    assert result[1].date == datetime(2020, 8, 31, 12, 0)
    assert result[1].split_ratio == 4.0
    mock_yfinance_repository.get_stock_splits.assert_called_once_with(symbol)
    mock_yfinance_client.get_stock_splits.assert_called_once_with(symbol)


def test_get_country_from_repository(yfinance_service, mock_yfinance_client, mock_yfinance_repository):
    """Test getting country from the repository when data exists."""
    # Setup
    symbol = "AAPL"
    mock_ticker_info = {"country": "United States", "region": "US"}
    mock_yfinance_repository.get_ticker_info.return_value = mock_ticker_info

    # Execute
    result = yfinance_service.get_country(symbol)

    # Verify
    assert isinstance(result, Country)
    assert result.iso_code == "US"
    mock_yfinance_repository.get_ticker_info.assert_called_once_with(symbol)
    mock_yfinance_client.get_ticker.assert_not_called()


def test_get_country_from_client(yfinance_service, mock_yfinance_client, mock_yfinance_repository):
    """Test getting country from client when repository has no data."""
    # Setup
    symbol = "AAPL"
    mock_yfinance_repository.get_ticker_info.return_value = None
    mock_ticker = MagicMock()
    mock_ticker.info = {"country": "United States", "region": "US"}
    mock_yfinance_client.get_ticker.return_value = mock_ticker

    # Execute
    result = yfinance_service.get_country(symbol)

    # Verify
    assert isinstance(result, Country)
    assert result.iso_code == "US"
    mock_yfinance_repository.get_ticker_info.assert_called_once_with(symbol)
    mock_yfinance_client.get_ticker.assert_called_once_with(symbol)


def test_get_country_from_region(yfinance_service, mock_yfinance_repository):
    """Test getting country from region when country is not available."""
    # Setup
    symbol = "AAPL"
    mock_ticker_info = {"region": "United States"}  # No country field
    mock_yfinance_repository.get_ticker_info.return_value = mock_ticker_info

    # Execute
    result = yfinance_service.get_country(symbol)

    # Verify
    assert isinstance(result, Country)
    assert result.iso_code == "US"


def test_get_country_none(yfinance_service, mock_yfinance_repository):
    """Test getting country when no country or region data is available."""
    # Setup
    symbol = "AAPL"
    mock_ticker_info = {}  # No country or region fields
    mock_yfinance_repository.get_ticker_info.return_value = mock_ticker_info

    # Execute
    result = yfinance_service.get_country(symbol)

    # Verify
    assert result is None


def test_get_sector_industry_from_repository(yfinance_service, mock_yfinance_client, mock_yfinance_repository):
    """Test getting sector and industry from repository when data exists."""
    # Setup
    symbol = "AAPL"
    mock_ticker_info = {"sector": "Technology", "industry": "Consumer Electronics"}
    mock_yfinance_repository.get_ticker_info.return_value = mock_ticker_info

    # Execute
    sector, industry = yfinance_service.get_sector_industry(symbol)

    # Verify
    assert sector == Sector.TECHNOLOGY
    assert industry == "Consumer Electronics"
    mock_yfinance_repository.get_ticker_info.assert_called_once_with(symbol)
    mock_yfinance_client.get_ticker.assert_not_called()


def test_get_sector_industry_from_client(yfinance_service, mock_yfinance_client, mock_yfinance_repository):
    """Test getting sector and industry from client when repository has no data."""
    # Setup
    symbol = "AAPL"
    mock_yfinance_repository.get_ticker_info.return_value = None
    mock_ticker = MagicMock()
    mock_ticker.info = {"sector": "Technology", "industry": "Consumer Electronics"}
    mock_yfinance_client.get_ticker.return_value = mock_ticker

    # Execute
    sector, industry = yfinance_service.get_sector_industry(symbol)

    # Verify
    assert sector == Sector.TECHNOLOGY
    assert industry == "Consumer Electronics"
    mock_yfinance_repository.get_ticker_info.assert_called_once_with(symbol)
    mock_yfinance_client.get_ticker.assert_called_once_with(symbol)


def test_get_sector_industry_unknown_sector(yfinance_service, mock_yfinance_repository):
    """Test getting sector and industry when sector is unknown."""
    # Setup
    symbol = "AAPL"
    mock_ticker_info = {"sector": "Unknown Sector", "industry": "Consumer Electronics"}
    mock_yfinance_repository.get_ticker_info.return_value = mock_ticker_info

    # Execute
    sector, industry = yfinance_service.get_sector_industry(symbol)

    # Verify
    assert sector == Sector.UNKNOWN
    assert industry is None


def test_get_sector_industry_missing_data(yfinance_service, mock_yfinance_repository):
    """Test getting sector and industry when data is missing."""
    # Setup
    symbol = "AAPL"
    mock_ticker_info = {}  # No sector or industry fields
    mock_yfinance_repository.get_ticker_info.return_value = mock_ticker_info

    # Execute
    sector, industry = yfinance_service.get_sector_industry(symbol)

    # Verify
    assert sector == Sector.UNKNOWN
    assert industry is None


def test_get_sector_industry_invalid_data(yfinance_service, mock_yfinance_repository):
    """Test getting sector and industry with invalid data."""
    # Setup
    symbol = "AAPL"
    mock_yfinance_repository.get_ticker_info.return_value = None

    # Execute
    sector, industry = yfinance_service.get_sector_industry(symbol)

    # Verify
    assert sector == Sector.UNKNOWN
    assert industry is None
