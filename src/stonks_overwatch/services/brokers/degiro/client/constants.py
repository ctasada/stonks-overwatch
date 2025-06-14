from enum import Enum


class TransactionType(Enum):
    """
    Enum representing various transaction types in DeGiro's API.

    - 0: Stock buy/sell
    - 101: Stock Split
    - 102: Dividend payment
    - 106: Corporate actions (e.g., stock splits, stock dividends)
    - 108: Fusion
    - 112: Delisting
    - 204: Swap stocks (PRODUCTWIJZIGING)
    """

    BUY_SELL = 0
    """Represents the buying or selling of a Stock."""

    STOCK_SPLIT = 101
    """Represents a Stock Split."""

    DIVIDEND = 102
    """Represents a Dividend payment."""

    CORPORATE_ACTION = 106  # Relates with Stock Dividends
    """Represents a Corporate action, such as stock splits, corporation rename or stock dividends."""

    FUSION = 108
    """Represents a Fusion, which is a type of corporate action where two companies merge."""

    DELISTING = 112
    """Represents a Delisting, which is the removal of a stock from an exchange or brokerage platform."""

    PRODUCT_CHANGE = 204
    """Represents a product change, such as a swap of stocks due to ISIN updates."""

    # INTEREST = 108 # Could be reverse split, but also stock dividends or interests
    # """Represents Interest payments, e.g., for margin or balances (transactionTypeId 108)."""
    #
    # WITHDRAWAL = 110 # Seems also related with stock dividends
    # """Represents Withdrawals from funds (transactionTypeId 110)."""
    #
    # FEES = 112 # Seems also related with stock dividends
    # """Represents Fees, such as transaction or management fees (transactionTypeId 112)."""
    #
    # DEPOSIT = 114 # Seems also related with stock dividends
    # """Represents Deposits into the trading account (transactionTypeId 114)."""

    # 108
    # 110
    # 112
    # 114
    # 204

    UNKNOWN = -1
    """Represents an unknown transaction type."""

    @staticmethod
    def from_int(value: int):
        try:
            return TransactionType(value)
        except ValueError:
            return TransactionType.UNKNOWN

    def to_string(self):
        readable_strings = {
            TransactionType.BUY_SELL: "",
            TransactionType.STOCK_SPLIT: "Stock Split",
            TransactionType.DIVIDEND: "Dividend Payment",
            TransactionType.CORPORATE_ACTION: "Corporate Action",
            TransactionType.PRODUCT_CHANGE: "Product Change",
            TransactionType.DELISTING: "Delisting",
            TransactionType.FUSION: "Fusion",
        }
        return readable_strings.get(self, "Unknown Transaction Type")


class ProductType(Enum):
    STOCK = 1
    """Represents a Stock product."""

    BONDS = 2
    FUTURES = 7
    OPTIONS = 8
    FUNDS = 13
    LEVERAGE_PRODUCTS = 14

    ETF = 131
    """Represents an ETF product."""

    INDEX = 180

    CASH = 311
    """Represents a Cash product."""

    CFDS = 535
    WARRANTS = 536

    UNKNOWN = -1
    """Represents an unknown product type."""

    @staticmethod
    def from_int(value: int):
        try:
            return ProductType(value)
        except ValueError:
            return ProductType.UNKNOWN

    def to_string(self) -> str:
        readable_strings = {
            ProductType.STOCK: "Stock",
            ProductType.ETF: "ETF",
            ProductType.CASH: "Cash",
        }
        return readable_strings.get(self, "Unknown Product Type")


class CurrencyFX(Enum):
    EUR_USD = 705366
    """Represents the EUR/USD ProductId"""

    @staticmethod
    def to_list() -> list[int]:
        return [member.value for member in CurrencyFX]

    @staticmethod
    def to_str_list() -> list[str]:
        return [str(member.value) for member in CurrencyFX]

    @staticmethod
    def known_currencies() -> list[str]:
        pairs = []

        for pair in CurrencyFX:
            # Extract the currencies from the enum name
            base, quote = pair.name.split("_")
            pairs.append(base)
            pairs.append(quote)

        known_currencies = list(set(pairs))
        known_currencies.sort()
        return known_currencies
