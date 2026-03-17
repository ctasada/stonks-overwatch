from stonks_overwatch.utils.currency import get_standard_currency, is_derived, normalize

import pytest


class TestNormalize:
    def test_normalize_gbx_to_gbp(self):
        amount, currency = normalize(100.0, "GBX")
        assert currency == "GBP"
        assert amount == pytest.approx(1.0)

    def test_normalize_standard_currency_unchanged(self):
        amount, currency = normalize(100.0, "EUR")
        assert currency == "EUR"
        assert amount == 100.0

    def test_normalize_usd_unchanged(self):
        amount, currency = normalize(50.0, "USD")
        assert currency == "USD"
        assert amount == 50.0

    def test_normalize_gbp_unchanged(self):
        amount, currency = normalize(75.0, "GBP")
        assert currency == "GBP"
        assert amount == 75.0

    def test_normalize_zero_amount(self):
        amount, currency = normalize(0.0, "GBX")
        assert currency == "GBP"
        assert amount == 0.0

    def test_normalize_large_amount(self):
        amount, currency = normalize(10000.0, "GBX")
        assert currency == "GBP"
        assert amount == pytest.approx(100.0)

    def test_normalize_negative_amount(self):
        """Short positions have negative quantities; normalization must preserve the sign."""
        amount, currency = normalize(-200.0, "GBX")
        assert currency == "GBP"
        assert amount == pytest.approx(-2.0)


class TestGetStandardCurrency:
    def test_gbx_returns_gbp(self):
        assert get_standard_currency("GBX") == "GBP"

    def test_standard_currency_returned_unchanged(self):
        assert get_standard_currency("EUR") == "EUR"
        assert get_standard_currency("USD") == "USD"
        assert get_standard_currency("GBP") == "GBP"
        assert get_standard_currency("NOK") == "NOK"

    def test_derived_new_currency_normalises_to_standard(self):
        """Passing a derived code as new_currency normalises it to the standard code.
        The caller receives a result in GBP, not GBX pence. This is the documented
        contract: new_currency must always be a standard ISO code."""
        assert get_standard_currency("GBX") == "GBP"


class TestIsDerived:
    def test_gbx_is_derived(self):
        assert is_derived("GBX") is True

    def test_standard_currencies_are_not_derived(self):
        assert is_derived("EUR") is False
        assert is_derived("USD") is False
        assert is_derived("GBP") is False
        assert is_derived("NOK") is False

    def test_empty_string_is_not_derived(self):
        assert is_derived("") is False

    def test_none_is_not_derived(self):
        # None is not a valid currency code but must not raise
        assert is_derived(None) is False
