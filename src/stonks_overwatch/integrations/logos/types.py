from enum import Enum


class LogoType(Enum):
    STOCK = "Stock"
    ETF = "ETF"
    CASH = "Cash"
    CRYPTO = "Crypto"
    COUNTRY = "Country"
    SECTOR = "Sector"
    UNKNOWN = "Unknown"

    @staticmethod
    def from_str(label: str) -> "LogoType":
        _map = {m.value.lower(): m for m in LogoType if m != LogoType.UNKNOWN}
        return _map.get(label.lower(), LogoType.UNKNOWN)
