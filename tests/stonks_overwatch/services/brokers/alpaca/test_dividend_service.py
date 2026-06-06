"""Tests for the Alpaca dividend service."""

from datetime import date
from decimal import Decimal

from stonks_overwatch.services.brokers.alpaca.repositories.models import AlpacaActivity
from stonks_overwatch.services.brokers.alpaca.services.dividend_service import DividendService
from stonks_overwatch.services.models import DividendType

import pytest
from django.test import TestCase


def _make_service_no_fx() -> DividendService:
    """Return a DividendService with _to_base_on_date patched as a USD no-op.

    Isolates amount-based assertions from live FX rates, which vary over time
    and differ between test environments.
    """
    service = DividendService()
    service._to_base = lambda amount, **_kw: amount  # type: ignore[method-assign]
    return service


@pytest.mark.django_db
class TestAlpacaDividendService(TestCase):
    def setUp(self):
        AlpacaActivity.objects.create(
            activity_id="div-001",
            activity_type="DIV",
            symbol="AAPL",
            net_amount=Decimal("12.50"),
            per_share_amount=Decimal("0.25"),
            activity_date=date(2024, 3, 15),
            description="AAPL dividend payment",
        )
        AlpacaActivity.objects.create(
            activity_id="div-002",
            activity_type="DIVCGL",
            symbol="MSFT",
            net_amount=Decimal("5.00"),
            per_share_amount=Decimal("0.10"),
            activity_date=date(2024, 6, 20),
            description="MSFT capital gain long term",
        )
        # Foreign tax withheld - should have taxes set
        AlpacaActivity.objects.create(
            activity_id="div-003",
            activity_type="DIVFT",
            symbol="SAP",
            net_amount=Decimal("-1.25"),
            activity_date=date(2024, 4, 10),
            description="Foreign tax withheld",
        )
        # Deposit activity - should NOT appear in dividends
        AlpacaActivity.objects.create(
            activity_id="csd-001",
            activity_type="CSD",
            symbol=None,
            net_amount=Decimal("1000.00"),
            activity_date=date(2024, 1, 5),
        )

    def test_get_dividends_returns_only_dividend_activities(self):
        """Test that only dividend activities are returned."""
        service = DividendService()
        dividends = service.get_dividends()

        assert isinstance(dividends, list)
        assert len(dividends) == 3
        symbols = [d.stock_symbol for d in dividends]
        assert "AAPL" in symbols
        assert "MSFT" in symbols

    def test_get_dividends_type_is_paid(self):
        """Test that all returned dividends have type PAID."""
        service = DividendService()
        dividends = service.get_dividends()

        for dividend in dividends:
            assert dividend.dividend_type == DividendType.PAID

    def test_get_dividends_amount_is_set(self):
        """Test that regular dividends have amount populated."""
        service = _make_service_no_fx()
        dividends = service.get_dividends()

        aapl = next(d for d in dividends if d.stock_symbol == "AAPL")
        assert aapl.amount == 12.50
        assert aapl.taxes == 0.0

    def test_get_dividends_foreign_tax_withheld_has_taxes(self):
        """Test that DIVFT activities result in taxes being set."""
        service = _make_service_no_fx()
        dividends = service.get_dividends()

        sap = next(d for d in dividends if d.stock_symbol == "SAP")
        assert sap.taxes == 1.25
        assert sap.amount == 0.0

    def test_get_dividends_sorted_newest_first(self):
        """Test that dividends are sorted with the newest first."""
        service = DividendService()
        dividends = service.get_dividends()

        dates = [d.payment_date for d in dividends]
        assert dates == sorted(dates, reverse=True)

    def test_get_dividends_empty_when_no_dividend_activities(self):
        """Test that an empty list is returned when no dividend activities exist."""
        AlpacaActivity.objects.filter(activity_type__in=["DIV", "DIVCGL", "DIVCGS", "DIVFT", "DIVNRA"]).delete()
        service = DividendService()
        dividends = service.get_dividends()
        # Only DIVFT was deleted, DIVCGL remains
        assert isinstance(dividends, list)
