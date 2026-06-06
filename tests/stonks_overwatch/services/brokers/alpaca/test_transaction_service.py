"""Tests for the Alpaca transaction service."""

from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from stonks_overwatch.services.brokers.alpaca.repositories.models import AlpacaOrder
from stonks_overwatch.services.brokers.alpaca.services.transaction_service import TransactionService

import pytest
from django.test import TestCase


def _make_service_no_fx() -> TransactionService:
    """Return a TransactionService with _to_base_on_date patched as a USD no-op.

    Isolates amount-based assertions from live FX rates, which vary over time
    and differ between test environments.
    """
    service = TransactionService()
    service._to_base = lambda amount, **_kw: amount  # type: ignore[method-assign]
    return service


@pytest.mark.django_db
class TestAlpacaTransactionService(TestCase):
    def setUp(self):
        AlpacaOrder.objects.create(
            order_id="order-001",
            symbol="AAPL",
            qty=Decimal("10"),
            filled_qty=Decimal("10"),
            filled_avg_price=Decimal("155.00"),
            side="buy",
            order_type="market",
            status="filled",
            submitted_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=dt_timezone.utc),
            filled_at=datetime(2024, 1, 15, 10, 1, 0, tzinfo=dt_timezone.utc),
        )
        AlpacaOrder.objects.create(
            order_id="order-002",
            symbol="TSLA",
            qty=Decimal("5"),
            filled_qty=Decimal("5"),
            filled_avg_price=Decimal("210.00"),
            side="sell",
            order_type="limit",
            status="filled",
            submitted_at=datetime(2024, 2, 20, 14, 0, 0, tzinfo=dt_timezone.utc),
            filled_at=datetime(2024, 2, 20, 14, 5, 0, tzinfo=dt_timezone.utc),
        )
        # This order should NOT appear since it's not filled
        AlpacaOrder.objects.create(
            order_id="order-003",
            symbol="GOOG",
            qty=Decimal("3"),
            filled_qty=None,
            filled_avg_price=None,
            side="buy",
            order_type="limit",
            status="canceled",
            submitted_at=datetime(2024, 3, 1, 9, 0, 0, tzinfo=dt_timezone.utc),
            filled_at=None,
        )

    def test_get_transactions_returns_only_filled_orders(self):
        """Test that only filled orders are returned as transactions."""
        service = TransactionService()
        transactions = service.get_transactions()

        assert isinstance(transactions, list)
        assert len(transactions) == 2
        symbols = [t.symbol for t in transactions]
        assert "AAPL" in symbols
        assert "TSLA" in symbols
        assert "GOOG" not in symbols

    def test_get_transactions_buy_sell_mapping(self):
        """Test that buy/sell sides are correctly mapped."""
        service = TransactionService()
        transactions = service.get_transactions()

        aapl = next(t for t in transactions if t.symbol == "AAPL")
        tsla = next(t for t in transactions if t.symbol == "TSLA")

        assert aapl.buy_sell == "Buy"
        assert tsla.buy_sell == "Sell"

    def test_get_transactions_calculates_total(self):
        """Test that total is calculated as filled_qty * filled_avg_price (USD identity, no FX)."""
        service = _make_service_no_fx()
        transactions = service.get_transactions()

        aapl = next(t for t in transactions if t.symbol == "AAPL")
        assert aapl.total == 10.0 * 155.0

    def test_get_transactions_empty_when_no_orders(self):
        """Test that an empty list is returned when there are no filled orders."""
        AlpacaOrder.objects.all().delete()
        service = TransactionService()
        transactions = service.get_transactions()
        assert transactions == []
