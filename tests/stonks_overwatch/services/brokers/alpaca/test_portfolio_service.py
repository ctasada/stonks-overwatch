"""Tests for the Alpaca portfolio service."""

from datetime import datetime, timezone as dt_tz
from decimal import Decimal

from stonks_overwatch.services.brokers.alpaca.repositories.models import AlpacaOrder, AlpacaPosition
from stonks_overwatch.services.brokers.alpaca.services.portfolio_service import PortfolioService

import pytest
from django.test import TestCase
from unittest.mock import MagicMock, patch


@pytest.mark.django_db
class TestAlpacaPortfolioService(TestCase):
    def setUp(self):
        AlpacaPosition.objects.create(
            symbol="AAPL",
            qty=Decimal("10"),
            avg_entry_price=Decimal("150.00"),
            market_value=Decimal("1650.00"),
            current_price=Decimal("165.00"),
            unrealized_pl=Decimal("150.00"),
            cost_basis=Decimal("1500.00"),
            side="long",
            currency="USD",
        )
        AlpacaPosition.objects.create(
            symbol="TSLA",
            qty=Decimal("5"),
            avg_entry_price=Decimal("200.00"),
            market_value=Decimal("1100.00"),
            current_price=Decimal("220.00"),
            unrealized_pl=Decimal("100.00"),
            cost_basis=Decimal("1000.00"),
            side="long",
            currency="USD",
        )

    @patch("stonks_overwatch.services.brokers.alpaca.services.portfolio_service.AlpacaClient")
    def test_get_portfolio_returns_entries(self, mock_client_class):
        """Test that get_portfolio returns a PortfolioEntry per position plus a cash entry."""
        mock_account = MagicMock()
        mock_account.cash = "5000.00"
        mock_client = MagicMock()
        mock_client.alpaca_config.offline_mode = False
        mock_client.get_latest_prices.return_value = {"AAPL": 170.0, "TSLA": 230.0}
        mock_client.get_account.return_value = mock_account
        mock_client_class.return_value = mock_client

        service = PortfolioService()
        portfolio = service.get_portfolio

        assert isinstance(portfolio, list)
        # 2 stock positions + 1 cash entry
        assert len(portfolio) == 3
        symbols = [e.symbol for e in portfolio]
        assert "AAPL" in symbols
        assert "TSLA" in symbols
        assert "USD" in symbols

    @patch("stonks_overwatch.services.brokers.alpaca.services.portfolio_service.AlpacaClient")
    def test_get_portfolio_sorted_by_symbol(self, mock_client_class):
        """Test that portfolio entries are sorted alphabetically by symbol."""
        mock_client = MagicMock()
        mock_client.alpaca_config.offline_mode = False
        mock_client.get_latest_prices.return_value = {}
        mock_client_class.return_value = mock_client

        service = PortfolioService()
        portfolio = service.get_portfolio

        symbols = [e.symbol for e in portfolio]
        assert symbols == sorted(symbols)

    @patch("stonks_overwatch.services.brokers.alpaca.services.portfolio_service.AlpacaClient")
    def test_get_portfolio_uses_stored_price_on_api_failure(self, mock_client_class):
        """Test that stored prices are used when the market data API fails."""
        mock_client = MagicMock()
        mock_client.alpaca_config.offline_mode = False
        mock_client.get_latest_prices.side_effect = RuntimeError("No credentials")
        mock_client_class.return_value = mock_client

        service = PortfolioService()
        portfolio = service.get_portfolio

        aapl = next(e for e in portfolio if e.symbol == "AAPL")
        assert aapl.price == 165.0

    @patch("stonks_overwatch.services.brokers.alpaca.services.portfolio_service.AlpacaClient")
    def test_get_portfolio_empty_when_no_positions(self, mock_client_class):
        """Test that only a cash entry is returned when no positions exist."""
        AlpacaPosition.objects.all().delete()

        mock_account = MagicMock()
        mock_account.cash = "100000.00"
        mock_client = MagicMock()
        mock_client.alpaca_config.offline_mode = False
        mock_client.get_account.return_value = mock_account
        mock_client_class.return_value = mock_client

        service = PortfolioService()
        portfolio = service.get_portfolio

        assert len(portfolio) == 1
        assert portfolio[0].symbol == "USD"
        assert portfolio[0].value == 100000.0

    @patch("stonks_overwatch.services.brokers.alpaca.services.portfolio_service.AlpacaClient")
    def test_get_portfolio_entry_values(self, mock_client_class):
        """Test that portfolio entry values are calculated correctly from latest prices."""
        mock_client = MagicMock()
        mock_client.alpaca_config.offline_mode = False
        mock_client.get_latest_prices.return_value = {"AAPL": 170.0, "TSLA": 230.0}
        mock_client_class.return_value = mock_client

        service = PortfolioService()
        portfolio = service.get_portfolio

        aapl = next(e for e in portfolio if e.symbol == "AAPL")
        assert aapl.price == 170.0
        assert aapl.value == 10.0 * 170.0
        assert aapl.shares == 10.0
        assert aapl.is_open is True

    @patch("stonks_overwatch.services.brokers.alpaca.services.deposit_service.DepositService.get_cash_deposits")
    @patch("stonks_overwatch.services.brokers.alpaca.services.portfolio_service.AlpacaClient")
    def test_get_portfolio_total_current_value_includes_cash(self, mock_client_class, mock_get_cash_deposits):
        """Test that current_value includes both stock positions and cash (consistent with DEGIRO)."""
        mock_account = MagicMock()
        mock_account.cash = "5000.00"
        mock_client = MagicMock()
        mock_client.get_latest_prices.return_value = {"AAPL": 170.0, "TSLA": 230.0}
        mock_client.get_account.return_value = mock_account
        mock_client_class.return_value = mock_client
        mock_get_cash_deposits.return_value = []

        service = PortfolioService()
        total = service.get_portfolio_total()

        # current_value = stocks (AAPL 10*170 + TSLA 5*230) + cash (5000)
        assert total.current_value > 0
        # cash is included in current_value
        assert total.total_cash > 0
        # current_value must be >= total_cash
        assert total.current_value >= total.total_cash

    @patch("stonks_overwatch.services.brokers.alpaca.services.deposit_service.DepositService.get_cash_deposits")
    @patch("stonks_overwatch.services.brokers.alpaca.services.portfolio_service.AlpacaClient")
    def test_get_portfolio_total_cash_only_account(self, mock_client_class, mock_get_cash_deposits):
        """Test that a cash-only account shows the cash as current_value (not zero)."""
        AlpacaPosition.objects.all().delete()

        mock_account = MagicMock()
        mock_account.cash = "100000.00"
        mock_client = MagicMock()
        mock_client.get_latest_prices.return_value = {}
        mock_client.get_account.return_value = mock_account
        mock_client_class.return_value = mock_client
        mock_get_cash_deposits.return_value = []

        service = PortfolioService()
        total = service.get_portfolio_total()

        # With no stock positions, current_value should equal total_cash (the USD balance)
        assert total.current_value > 0
        assert total.total_cash > 0
        assert total.current_value == total.total_cash


_T1 = datetime(2024, 1, 10, 10, 0, tzinfo=dt_tz.utc)
_T2 = datetime(2024, 3, 5, 14, 0, tzinfo=dt_tz.utc)


@pytest.mark.django_db
class TestAlpacaClosedPositions(TestCase):
    """Tests for _compute_closed_positions() and its integration with get_portfolio."""

    def _make_order(self, order_id, symbol, side, qty, price, filled_at):
        return AlpacaOrder.objects.create(
            order_id=order_id,
            symbol=symbol,
            side=side,
            qty=Decimal(str(qty)),
            filled_qty=Decimal(str(qty)),
            filled_avg_price=Decimal(str(price)),
            order_type="market",
            status="filled",
            submitted_at=filled_at,
            filled_at=filled_at,
        )

    def _make_service(self):
        """Return a PortfolioService with AlpacaClient fully mocked."""
        with patch("stonks_overwatch.services.brokers.alpaca.services.portfolio_service.AlpacaClient") as cls:
            mock_client = MagicMock()
            mock_client.get_latest_prices.return_value = {}
            mock_client.get_account.return_value = MagicMock(cash="0")
            cls.return_value = mock_client
            service = PortfolioService()
        return service

    @patch("stonks_overwatch.services.brokers.alpaca.services.portfolio_service.AlpacaClient")
    def test_closed_position_appears_with_is_open_false(self, mock_client_class):
        """A fully sold symbol with no current open position shows up as is_open=False."""
        mock_client = MagicMock()
        mock_client.get_latest_prices.return_value = {}
        mock_client.get_account.return_value = MagicMock(cash="0")
        mock_client_class.return_value = mock_client

        # No open positions for NVDA
        AlpacaPosition.objects.all().delete()
        self._make_order("o1", "NVDA", "buy", 10, 400.0, _T1)
        self._make_order("o2", "NVDA", "sell", 10, 450.0, _T2)

        service = PortfolioService()
        portfolio = service.get_portfolio

        nvda = next((e for e in portfolio if e.symbol == "NVDA"), None)
        assert nvda is not None
        assert nvda.is_open is False
        assert nvda.shares == 0.0

    @patch("stonks_overwatch.services.brokers.alpaca.services.portfolio_service.AlpacaClient")
    def test_closed_position_fifo_realized_gain(self, mock_client_class):
        """FIFO gain: buy 10 @ $400, sell 10 @ $450 → realized gain = $500 USD."""
        mock_client = MagicMock()
        mock_client.get_latest_prices.return_value = {}
        mock_client.get_account.return_value = MagicMock(cash="0")
        mock_client_class.return_value = mock_client

        AlpacaPosition.objects.all().delete()
        self._make_order("o3", "MSFT", "buy", 10, 400.0, _T1)
        self._make_order("o4", "MSFT", "sell", 10, 450.0, _T2)

        service = PortfolioService()
        # Patch _to_base so amounts stay in USD regardless of test environment currency
        with patch.object(service, "_to_base", side_effect=lambda x: x):
            closed = [e for e in service._compute_closed_positions() if e.symbol == "MSFT"]

        assert len(closed) == 1
        assert abs(closed[0].realized_gain - 500.0) < 0.01
        assert abs(closed[0].total_costs - 4000.0) < 0.01

    @patch("stonks_overwatch.services.brokers.alpaca.services.portfolio_service.AlpacaClient")
    def test_closed_position_fifo_multiple_buy_lots(self, mock_client_class):
        """FIFO across two buy lots: buy 5@$100 then 5@$200, sell 10@$300 → gain = $1500."""
        mock_client = MagicMock()
        mock_client.get_latest_prices.return_value = {}
        mock_client.get_account.return_value = MagicMock(cash="0")
        mock_client_class.return_value = mock_client

        AlpacaPosition.objects.all().delete()
        t0 = datetime(2024, 1, 1, tzinfo=dt_tz.utc)
        t1 = datetime(2024, 2, 1, tzinfo=dt_tz.utc)
        t2 = datetime(2024, 3, 1, tzinfo=dt_tz.utc)
        self._make_order("o5", "AMD", "buy", 5, 100.0, t0)
        self._make_order("o6", "AMD", "buy", 5, 200.0, t1)
        self._make_order("o7", "AMD", "sell", 10, 300.0, t2)

        service = PortfolioService()
        with patch.object(service, "_to_base", side_effect=lambda x: x):
            closed = [e for e in service._compute_closed_positions() if e.symbol == "AMD"]

        assert len(closed) == 1
        # FIFO: 5*(300-100) + 5*(300-200) = 1000 + 500 = 1500
        assert abs(closed[0].realized_gain - 1500.0) < 0.01
        assert abs(closed[0].total_costs - 1500.0) < 0.01

    @patch("stonks_overwatch.services.brokers.alpaca.services.portfolio_service.AlpacaClient")
    def test_partially_closed_symbol_not_in_closed_list(self, mock_client_class):
        """A symbol still held (net qty > 0) must not appear as a closed position."""
        mock_client = MagicMock()
        mock_client.get_latest_prices.return_value = {}
        mock_client.get_account.return_value = MagicMock(cash="0")
        mock_client_class.return_value = mock_client

        AlpacaPosition.objects.all().delete()
        # Buy 10, sell only 5 → still holding 5
        self._make_order("o8", "GOOG", "buy", 10, 150.0, _T1)
        self._make_order("o9", "GOOG", "sell", 5, 180.0, _T2)

        service = PortfolioService()
        closed = [e for e in service.get_portfolio if not e.is_open and e.symbol == "GOOG"]

        assert len(closed) == 0

    @patch("stonks_overwatch.services.brokers.alpaca.services.portfolio_service.AlpacaClient")
    def test_open_position_symbol_excluded_from_closed(self, mock_client_class):
        """A symbol with an open AlpacaPosition row must never appear as closed."""
        mock_client = MagicMock()
        mock_client.get_latest_prices.return_value = {"AAPL": 170.0}
        mock_client.get_account.return_value = MagicMock(cash="0")
        mock_client_class.return_value = mock_client

        AlpacaPosition.objects.all().delete()
        # AAPL still open — create the position explicitly for this test class
        AlpacaPosition.objects.create(
            symbol="AAPL",
            qty=Decimal("10"),
            avg_entry_price=Decimal("150.00"),
            current_price=Decimal("170.00"),
            side="long",
            currency="USD",
        )
        # Add orders that net to 0 — but the open-position check must win
        self._make_order("o10", "AAPL", "buy", 10, 150.0, _T1)
        self._make_order("o11", "AAPL", "sell", 10, 170.0, _T2)

        service = PortfolioService()
        closed = [e for e in service.get_portfolio if not e.is_open and e.symbol == "AAPL"]

        assert len(closed) == 0

    @patch("stonks_overwatch.services.brokers.alpaca.services.portfolio_service.AlpacaClient")
    def test_no_orders_returns_empty_closed_list(self, mock_client_class):
        """With no filled orders the closed positions list is empty."""
        mock_client = MagicMock()
        mock_client.get_latest_prices.return_value = {}
        mock_client.get_account.return_value = MagicMock(cash="0")
        mock_client_class.return_value = mock_client

        AlpacaPosition.objects.all().delete()

        service = PortfolioService()
        closed = [e for e in service.get_portfolio if not e.is_open]

        assert closed == []
