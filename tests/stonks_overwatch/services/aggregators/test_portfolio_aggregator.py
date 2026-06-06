from stonks_overwatch.services.aggregators.portfolio_aggregator import PortfolioAggregatorService
from stonks_overwatch.services.models import PortfolioEntry
from stonks_overwatch.utils.domain.constants import ProductType

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def aggregator():
    with patch("stonks_overwatch.services.aggregators.portfolio_aggregator.YFinance") as mock_yf_class:
        mock_yf = MagicMock()
        mock_yf_class.return_value = mock_yf
        svc = PortfolioAggregatorService()
        svc.yfinance = mock_yf
        yield svc, mock_yf


class TestAssignName:
    """Tests for PortfolioAggregatorService._assign_name()."""

    def test_resolves_name_when_name_equals_symbol(self, aggregator):
        """Name is replaced with the full company name when it currently matches the ticker."""
        svc, mock_yf = aggregator
        mock_yf.get_name.return_value = "Apple Inc."
        entry = PortfolioEntry(symbol="AAPL", name="AAPL", product_type=ProductType.STOCK)

        svc._assign_name(entry)

        assert entry.name == "Apple Inc."
        mock_yf.get_name.assert_called_once_with("AAPL")

    def test_resolves_name_when_name_is_empty(self, aggregator):
        """Name is filled in when the broker left it blank."""
        svc, mock_yf = aggregator
        mock_yf.get_name.return_value = "Tesla Inc."
        entry = PortfolioEntry(symbol="TSLA", name="", product_type=ProductType.STOCK)

        svc._assign_name(entry)

        assert entry.name == "Tesla Inc."

    def test_does_not_overwrite_existing_name(self, aggregator):
        """A name already set by the broker (e.g. DEGIRO) is not replaced."""
        svc, mock_yf = aggregator
        entry = PortfolioEntry(symbol="AAPL", name="Apple Inc.", product_type=ProductType.STOCK)

        svc._assign_name(entry)

        assert entry.name == "Apple Inc."
        mock_yf.get_name.assert_not_called()

    def test_skips_cash_entries(self, aggregator):
        """Cash entries are never looked up in yfinance."""
        svc, mock_yf = aggregator
        entry = PortfolioEntry(symbol="USD", name="USD", product_type=ProductType.CASH)

        svc._assign_name(entry)

        mock_yf.get_name.assert_not_called()

    def test_skips_crypto_entries(self, aggregator):
        """Crypto entries are never looked up in yfinance."""
        svc, mock_yf = aggregator
        entry = PortfolioEntry(symbol="BTC", name="BTC", product_type=ProductType.CRYPTO)

        svc._assign_name(entry)

        mock_yf.get_name.assert_not_called()

    def test_resolves_name_for_etf(self, aggregator):
        """ETF entries are enriched the same as stocks."""
        svc, mock_yf = aggregator
        mock_yf.get_name.return_value = "iShares Core S&P 500 ETF"
        entry = PortfolioEntry(symbol="IVV", name="IVV", product_type=ProductType.ETF)

        svc._assign_name(entry)

        assert entry.name == "iShares Core S&P 500 ETF"

    def test_keeps_symbol_when_yfinance_returns_none(self, aggregator):
        """If yfinance has no name, the existing value (ticker) is preserved."""
        svc, mock_yf = aggregator
        mock_yf.get_name.return_value = None
        entry = PortfolioEntry(symbol="XYZ", name="XYZ", product_type=ProductType.STOCK)

        svc._assign_name(entry)

        assert entry.name == "XYZ"
