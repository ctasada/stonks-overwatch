"""Tests for the Alpaca deposit service."""

from datetime import date
from decimal import Decimal

from stonks_overwatch.services.brokers.alpaca.repositories.models import AlpacaActivity
from stonks_overwatch.services.brokers.alpaca.services.deposit_service import DepositService
from stonks_overwatch.services.models import DepositType

import pytest
from django.test import TestCase
from unittest.mock import MagicMock, patch


def _make_service_no_fx() -> DepositService:
    """Return a DepositService with _to_base patched as a USD no-op (identity function).

    This isolates amount-based assertions from real FX rates, which vary over
    time and differ between test environments.
    """
    service = DepositService()
    service._to_base = lambda amount, **_kw: amount  # type: ignore[method-assign]
    return service


@pytest.mark.django_db
class TestAlpacaDepositService(TestCase):
    def setUp(self):
        AlpacaActivity.objects.create(
            activity_id="act-csd-001",
            activity_type="CSD",
            symbol=None,
            net_amount=Decimal("5000.00"),
            activity_date=date(2024, 1, 10),
            description="Cash Deposit",
        )
        AlpacaActivity.objects.create(
            activity_id="act-csw-001",
            activity_type="CSW",
            symbol=None,
            net_amount=Decimal("-500.00"),
            activity_date=date(2024, 2, 15),
            description="Cash Withdrawal",
        )
        # Dividend activity — must NOT appear in deposits
        AlpacaActivity.objects.create(
            activity_id="act-div-001",
            activity_type="DIV",
            symbol="AAPL",
            net_amount=Decimal("12.50"),
            per_share_amount=Decimal("0.25"),
            activity_date=date(2024, 3, 1),
        )

    def test_get_cash_deposits_returns_only_deposit_activities(self):
        """Test that only deposit/withdrawal activities are returned."""
        service = _make_service_no_fx()
        deposits = service.get_cash_deposits()

        assert isinstance(deposits, list)
        assert len(deposits) == 2

    def test_get_cash_deposits_positive_amount_is_deposit(self):
        """Test that a positive net_amount maps to DepositType.DEPOSIT."""
        service = _make_service_no_fx()
        deposits = service.get_cash_deposits()

        deposit = next(d for d in deposits if d.change > 0)
        assert deposit.type == DepositType.DEPOSIT
        assert deposit.change == 5000.0

    def test_get_cash_deposits_negative_amount_is_withdrawal(self):
        """Test that a negative net_amount maps to DepositType.WITHDRAWAL."""
        service = _make_service_no_fx()
        deposits = service.get_cash_deposits()

        withdrawal = next(d for d in deposits if d.change < 0)
        assert withdrawal.type == DepositType.WITHDRAWAL
        assert withdrawal.change == -500.0

    def test_calculate_cash_account_value_cumulative(self):
        """Test that cash account value accumulates deposits and withdrawals."""
        service = _make_service_no_fx()
        cash_account = service.calculate_cash_account_value()

        assert isinstance(cash_account, dict)
        assert "2024-01-10" in cash_account
        assert cash_account["2024-01-10"] == 5000.0
        assert "2024-02-15" in cash_account
        assert cash_account["2024-02-15"] == 4500.0

    def test_get_cash_deposits_empty_when_no_deposit_activities(self):
        """Test that empty list is returned when no deposit activities exist."""
        AlpacaActivity.objects.filter(activity_type__in=["CSD", "CSW", "TRANS"]).delete()
        service = _make_service_no_fx()
        deposits = service.get_cash_deposits()
        assert deposits == []

    def test_get_cash_deposits_includes_jnlc_as_deposit(self):
        """Test that JNLC (journal cash) with positive net_amount is treated as a deposit."""
        AlpacaActivity.objects.create(
            activity_id="act-jnlc-001",
            activity_type="JNLC",
            symbol=None,
            net_amount=Decimal("1000.00"),
            activity_date=date(2024, 4, 1),
            description="Journal Cash Transfer In",
        )
        service = _make_service_no_fx()
        deposits = service.get_cash_deposits()

        jnlc = next((d for d in deposits if d.change == 1000.0), None)
        assert jnlc is not None
        assert jnlc.type == DepositType.DEPOSIT

    def test_get_cash_deposits_includes_jnlc_as_withdrawal(self):
        """Test that JNLC with negative net_amount is treated as a withdrawal."""
        AlpacaActivity.objects.create(
            activity_id="act-jnlc-002",
            activity_type="JNLC",
            symbol=None,
            net_amount=Decimal("-250.00"),
            activity_date=date(2024, 4, 2),
            description="Journal Cash Transfer Out",
        )
        service = _make_service_no_fx()
        deposits = service.get_cash_deposits()

        jnlc = next((d for d in deposits if d.change == -250.0), None)
        assert jnlc is not None
        assert jnlc.type == DepositType.WITHDRAWAL

    def test_get_cash_deposits_converts_usd_to_base_currency_using_historical_rate(self):
        """Test that net_amount (USD) is converted to base_currency at the activity date rate."""
        service = DepositService()
        mock_fx = MagicMock()
        mock_fx.convert.return_value = 4600.0
        service._fx = mock_fx

        with patch.object(type(service), "base_currency", new_callable=lambda: property(lambda _: "EUR")):
            deposits = service.get_cash_deposits()

        deposit = next(d for d in deposits if d.type == DepositType.DEPOSIT)
        mock_fx.convert.assert_any_call(5000.0, "USD", "EUR", date=date(2024, 1, 10))
        assert deposit.change == 4600.0
        assert deposit.currency == "EUR"

    def test_get_cash_deposits_no_conversion_when_base_currency_is_usd(self):
        """Test that CurrencyConverter is not called when base_currency is already USD."""
        service = DepositService()
        mock_fx = MagicMock()
        service._fx = mock_fx

        with patch.object(type(service), "base_currency", new_callable=lambda: property(lambda _: "USD")):
            deposits = service.get_cash_deposits()

        mock_fx.convert.assert_not_called()
        deposit = next(d for d in deposits if d.type == DepositType.DEPOSIT)
        assert deposit.change == 5000.0
        assert deposit.currency == "USD"
