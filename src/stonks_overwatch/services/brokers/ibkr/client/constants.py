from enum import Enum


class AssetClass(Enum):
    STOCK = "STK"
    OPTION = "OPT"
    FUTURE = "FUT"
    CFD = "CFD"
    WARRANT = "WAR"
    FOREX = "SWP"
    MUTUAL_FUND = "FND"
    BOND = "BND"
    INTER_COMMODITY_SPREAD = "ICS"
    UNKNOWN = "UNKNOWN"
    """Represents an unknown product type."""

    @staticmethod
    def from_string(value: str):
        try:
            return AssetClass(value)
        except ValueError:
            return AssetClass.UNKNOWN

    def to_string(self) -> str:
        readable_strings = {
            AssetClass.STOCK: "Stock",
            AssetClass.OPTION: "Option",
            AssetClass.FUTURE: "Future",
            AssetClass.CFD: "CFD",
            AssetClass.WARRANT: "Warrant",
            AssetClass.FOREX: "Forex",
            AssetClass.MUTUAL_FUND: "Mutual Fund",
            AssetClass.BOND: "Bond",
            AssetClass.INTER_COMMODITY_SPREAD: "Inter-Commodity Spread",
        }
        return readable_strings.get(self, "Unknown Product Type")


class TransactionType(Enum):
    BUY = "Buy"
    SELL = "Sell"
    DIVIDEND_PAYMENT = "Dividend Payment"
    UNKNOWN = "UNKNOWN"
    """Represents an unknown product type."""

    @staticmethod
    def from_string(value: str):
        try:
            return TransactionType(value)
        except ValueError:
            return TransactionType.UNKNOWN

    def to_string(self) -> str:
        readable_strings = {
            TransactionType.BUY: "Buy",
            TransactionType.SELL: "Sell",
            TransactionType.DIVIDEND_PAYMENT: "Dividend Payment",
        }
        return readable_strings.get(self, "Unknown Product Type")
