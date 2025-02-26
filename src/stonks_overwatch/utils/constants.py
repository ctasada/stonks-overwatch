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

class Sector(Enum):
    TECHNOLOGY = "Technology"
    FINANCIAL_SERVICES = "Financial Services"
    HEALTHCARE = "Healthcare"
    CONSUMER_CYCLICAL = "Consumer Cyclical"
    COMMUNICATION_SERVICES = "Communication Services"
    BASIC_MATERIALS = "Basic Materials"
    INDUSTRIALS = "Industrials"
    REAL_ESTATE = "Real Estate"
    CONSUMER_DEFENSIVE = "Consumer Defensive"
    UTILITIES = "Utilities"
    ENERGY = "Energy"
    UNKNOWN = "Unknown"

    @staticmethod
    def from_str(label: str|None):  # noqa: C901
        if not label:
            return Sector.UNKNOWN

        value = label.lower()
        if value == "technology":
            return Sector.TECHNOLOGY
        elif value in ["financial", "financial services"]:
            return Sector.FINANCIAL_SERVICES
        elif value == "healthcare":
            return Sector.HEALTHCARE
        elif value == "consumer cyclical":
            return Sector.CONSUMER_CYCLICAL
        elif value in ["communication services", "services", "communications"]:
            return Sector.COMMUNICATION_SERVICES
        elif value == "basic materials":
            return Sector.BASIC_MATERIALS
        elif value in ["industrial", "industrials"]:
            return Sector.INDUSTRIALS
        elif value == "real estate":
            return Sector.REAL_ESTATE
        elif value in ["consumer defensive", "consumer/non-cyclical", "consumer, non-cyclical"]:
            return Sector.CONSUMER_DEFENSIVE
        elif value == "utilities":
            return Sector.UTILITIES
        elif value == "energy":
            return Sector.ENERGY

        raise ValueError(f"Unknown sector: {label}")
