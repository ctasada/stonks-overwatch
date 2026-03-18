"""
DeGiro transaction description patterns.

DeGiro writes transaction descriptions in the language of the user's account settings,
so the same transaction type may appear with different descriptions depending on the locale.

To add support for a new language, find the relevant constant below and append the new
description strings with a language comment. Each constant's docstring explains which part
of the system uses it, so the impact of any change is immediately visible.
"""

from stonks_overwatch.services.models import FeeType

# Descriptions DeGiro uses for cash deposits and withdrawals.
# Used in CashMovementsRepository to filter deposit rows and compute the total deposited amount.
# FIXME: DeGiro doesn't have a consistent description or type for these transactions.
DEPOSIT_DESCRIPTIONS: frozenset[str] = frozenset(
    [
        # Dutch (NL)
        "iDEAL storting",
        "Terugstorting",
        "flatex terugstorting",
        # English (EN)
        "iDEAL Deposit",
        "Processed Flatex Withdrawal",
        # German (DE)
        "SOFORT Einzahlung",
        "Soforteinzahlung",
        "flatex Auszahlung",
        "flatex Einzahlung",
    ]
)

# Descriptions DeGiro uses for dividend-related transactions.
# Used in DividendsService to identify dividend income and tax withholding rows.
# Positive amounts are counted as income; negative amounts as taxes withheld.
DIVIDEND_DESCRIPTIONS: frozenset[str] = frozenset(
    [
        # Dutch (NL)
        "Dividend",
        "Dividendbelasting",
        "Vermogenswinst",
        # German (DE)
        "Dividende",
        "Dividendensteuer",
        "Kapitalrückzahlung",
        "Barausgleich Kapitalmaßnahme (Aktie)",
        # English (EN) — add here when discovered
    ]
)

# Substring patterns used to classify account fee types.
# Used in FeesService.__get_fee_type() — a description matches a FeeType if it contains
# any of the strings in the corresponding set.
# To add a new language variant, append the new substring to the relevant FeeType set.
FEE_TYPE_PATTERNS: dict[FeeType, frozenset[str]] = {
    FeeType.FINANCE_TRANSACTION_TAX: frozenset(
        [
            "Transaction Tax",  # English (EN) — e.g. "Spanish Transaction Tax"
        ]
    ),
    FeeType.CONNECTION: frozenset(
        [
            "DEGIRO Aansluitingskosten",  # Dutch (NL)
        ]
    ),
    FeeType.ADR_GDR: frozenset(
        [
            "ADR/GDR Externe Kosten",  # Dutch (NL)
            "ADR/GDR Weitergabegebühr",  # German (DE)
        ]
    ),
}
