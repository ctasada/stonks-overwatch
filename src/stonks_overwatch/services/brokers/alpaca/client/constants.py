"""Constants for the Alpaca broker integration."""

from enum import Enum

_ACTIVITY_LABELS: dict[str, str] = {
    "FILL": "Order fill",
    "OPTRD": "Option trade",
    "TRANS": "Cash transaction",
    "CSD": "Cash deposit",
    "CSW": "Cash withdrawal",
    "JNL": "Journal entry",
    "JNLC": "Journal entry (cash)",
    "JNLS": "Journal entry (stock)",
    "DIV": "Dividend",
    "DIVCGL": "Dividend – capital gain (long term)",
    "DIVCGS": "Dividend – capital gain (short term)",
    "DIVFEE": "Dividend fee",
    "DIVFT": "Dividend – foreign tax withheld",
    "DIVNRA": "Dividend – NRA withheld",
    "DIVROC": "Dividend – return of capital",
    "DIVTW": "Dividend – Tefra withheld",
    "DIVTXEX": "Dividend (tax exempt)",
    "CGD": "Capital gain distribution",
    "INT": "Interest",
    "INTNRA": "Interest – NRA withheld",
    "INTTW": "Interest – Tefra withheld",
    "FEE": "Fee",
    "CFEE": "Crypto fee",
    "PTC": "Pass-thru charge",
    "PTR": "Pass-thru rebate",
    "ACATC": "ACATS transfer (cash)",
    "ACATS": "ACATS transfer (securities)",
    "FOPT": "Free of payment transfer",
    "MA": "Merger / acquisition",
    "NC": "Name change",
    "REORG": "Reorganisation",
    "SPIN": "Stock spinoff",
    "SPLIT": "Stock split",
    "OPASN": "Option assignment",
    "OPCA": "Option corporate action",
    "OPCSH": "Option cash deliverable",
    "OPEXC": "Option exercise",
    "OPEXP": "Option expiration",
    "MISC": "Miscellaneous",
}


class ActivityType(str, Enum):
    """
    Alpaca account activity types.

    Source: https://docs.alpaca.markets/us/openapi/trading-api.json
    """

    # --- Trade fills ---
    FILL = "FILL"
    OPTRD = "OPTRD"

    # --- Cash transactions ---
    TRANS = "TRANS"
    CSD = "CSD"
    CSW = "CSW"

    # --- Journal entries ---
    JNL = "JNL"
    JNLC = "JNLC"
    JNLS = "JNLS"

    # --- Dividends ---
    DIV = "DIV"
    DIVCGL = "DIVCGL"
    DIVCGS = "DIVCGS"
    DIVFEE = "DIVFEE"
    DIVFT = "DIVFT"
    DIVNRA = "DIVNRA"
    DIVROC = "DIVROC"
    DIVTW = "DIVTW"
    DIVTXEX = "DIVTXEX"
    CGD = "CGD"

    # --- Interest ---
    INT = "INT"
    INTNRA = "INTNRA"
    INTTW = "INTTW"

    # --- Fees & charges ---
    FEE = "FEE"
    CFEE = "CFEE"
    PTC = "PTC"
    PTR = "PTR"

    # --- ACATS transfers ---
    ACATC = "ACATC"
    ACATS = "ACATS"

    # --- Free of payment transfers ---
    FOPT = "FOPT"

    # --- Corporate actions ---
    MA = "MA"
    NC = "NC"
    REORG = "REORG"
    SPIN = "SPIN"
    SPLIT = "SPLIT"

    # --- Options corporate actions ---
    OPASN = "OPASN"
    OPCA = "OPCA"
    OPCSH = "OPCSH"
    OPEXC = "OPEXC"
    OPEXP = "OPEXP"

    # --- Miscellaneous ---
    MISC = "MISC"

    @property
    def label(self) -> str:
        """Return a human-readable label for this activity type."""
        return _ACTIVITY_LABELS.get(self.value, self.value)


DIVIDEND_ACTIVITY_TYPES = [
    ActivityType.DIV,
    ActivityType.DIVCGL,
    ActivityType.DIVCGS,
    ActivityType.DIVFEE,
    ActivityType.DIVFT,
    ActivityType.DIVNRA,
    ActivityType.DIVROC,
    ActivityType.DIVTW,
    ActivityType.DIVTXEX,
    ActivityType.CGD,
]

DEPOSIT_ACTIVITY_TYPES = [
    ActivityType.CSD,  # Cash deposit
    ActivityType.CSW,  # Cash withdrawal
    ActivityType.TRANS,  # Generic cash transaction
    ActivityType.JNLC,  # Journal entry (cash) — moves cash between accounts
    ActivityType.JNL,  # Journal entry (generic) — may carry a net_amount
]

ALPACA_BASE_URL = "https://api.alpaca.markets"
ALPACA_PAPER_BASE_URL = "https://paper-api.alpaca.markets"
