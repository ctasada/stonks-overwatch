from typing import List

from stonks_overwatch.services.brokers.yfinance.client.yfinance_client import StockSplit, YFinanceClient
from stonks_overwatch.services.brokers.yfinance.repositories.yfinance_repository import YFinanceRepository
from stonks_overwatch.services.models import Country, Sector
from stonks_overwatch.utils.core.logger import StonksLogger


class YFinance:
    logger = StonksLogger.get_logger("stonks_overwatch.yfinance", "[YFINANCE|SERVICE]")

    def __init__(self):
        self.client = YFinanceClient()
        self.repository = YFinanceRepository()

    def get_stock_splits(self, symbol: str) -> List[StockSplit]:
        """Get stock splits for a given ticker. Retrieves the data from the DB, if not found,
        fetches it from Yahoo Finance.

        Args:
            symbol (str): Stock ticker. Symbol

        Returns:
            List[StockSplit]: List of stock splits
        """
        self.logger.debug(f"Get Stock Splits for {symbol}")

        splits = self.repository.get_stock_splits(symbol)
        if splits is None:
            splits = self.client.get_stock_splits(symbol)
            # self.repository.save_stock_splits(symbol, splits)
        else:
            splits = [StockSplit.from_dict(split) for split in splits]

        return splits

    def get_country(self, symbol: str) -> Country | None:
        ticker_info = self.repository.get_ticker_info(symbol)
        if ticker_info is None:
            ticker = self.client.get_ticker(symbol)
            ticker_info = ticker.info

        try:
            if ticker_info.get("country"):
                return Country(ticker_info["country"])

            if ticker_info.get("region"):
                return Country(ticker_info["region"])
        except AttributeError:
            pass

        return None

    def get_sector_industry(self, symbol: str) -> tuple[Sector, str | None]:
        ticker_info = self.repository.get_ticker_info(symbol)
        if ticker_info is None:
            ticker = self.client.get_ticker(symbol)
            ticker_info = ticker.info

        try:
            sector = Sector(ticker_info.get("sector")) if ticker_info.get("sector") else Sector.UNKNOWN
            industry = ticker_info.get("industry")
            return sector, industry
        except (AttributeError, ValueError):
            return Sector.UNKNOWN, None
