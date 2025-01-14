from enum import Enum


class ProductType(Enum):
    STOCK = "Stock"
    ETF = "ETF"
    CASH = "Cash"
    CRYPTO = "Crypto"

    UNKNOWN = "Unknown"

    @staticmethod
    def from_str(label: str):
        value = label.lower()
        if value == "stock":
            return ProductType.STOCK
        elif value == "etf":
            return ProductType.ETF
        elif value == "cash":
            return ProductType.CASH
        elif value == "crypto":
            return ProductType.CRYPTO

        return ProductType.UNKNOWN
