"""
Currency normalization utilities.

Handles derived and non-standard currency codes by mapping them to their
standard ISO equivalents before conversion.
"""

# Maps non-standard or derived currency codes to (standard_currency, conversion_factor).
# Example: GBX (British pence) = 1/100 of GBP.
# "GBX" is the representation used by DeGiro and most European exchanges for British pence.
_DERIVED_CURRENCIES: dict[str, tuple[str, float]] = {
    "GBX": ("GBP", 0.01),
}


def normalize(amount: float, currency: str | None) -> tuple[float, str | None]:
    """
    Normalize a derived currency to its standard equivalent.

    Converts non-standard currency codes (e.g. GBX pence) to their standard ISO
    equivalent (e.g. GBP pounds) by applying a conversion factor.

    Args:
        amount: The monetary amount in the given currency.
        currency: The currency code (may be a derived currency like GBX).

    Returns:
        Tuple of (normalized_amount, standard_currency_code).
    """
    if currency and currency in _DERIVED_CURRENCIES:
        standard_currency, factor = _DERIVED_CURRENCIES[currency]
        return amount * factor, standard_currency
    return amount, currency


def get_standard_currency(currency: str | None) -> str | None:
    """
    Get the standard ISO currency code for a given currency.

    Args:
        currency: The currency code (may be a derived currency like GBX).

    Returns:
        Standard ISO currency code (e.g. GBP for GBX), or the input unchanged.
    """
    if currency and currency in _DERIVED_CURRENCIES:
        return _DERIVED_CURRENCIES[currency][0]
    return currency


def is_derived(currency: str | None) -> bool:
    """
    Check if a currency is a derived (non-standard) currency.

    Args:
        currency: The currency code to check.

    Returns:
        True if the currency is derived (e.g. GBX), False otherwise.
    """
    return bool(currency) and currency in _DERIVED_CURRENCIES
