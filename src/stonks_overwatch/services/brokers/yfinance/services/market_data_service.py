import time
from typing import List

from yfinance.exceptions import YFRateLimitError

from stonks_overwatch.services.brokers.yfinance.client.yfinance_client import StockSplit, YFinanceClient
from stonks_overwatch.services.brokers.yfinance.repositories.yfinance_repository import YFinanceRepository
from stonks_overwatch.services.models import Country, Sector
from stonks_overwatch.utils.core.logger import StonksLogger


class YFinance:
    logger = StonksLogger.get_logger("stonks_overwatch.yfinance", "[YFINANCE|SERVICE]")

    def __init__(self):
        self.client = YFinanceClient()
        self.repository = YFinanceRepository()

    def _get_ticker_info_with_retry(self, symbol: str, max_retries: int = 3) -> dict | None:
        """
        Get ticker info with exponential backoff retry logic for rate limit errors.

        Args:
            symbol: Stock ticker symbol
            max_retries: Maximum number of retry attempts

        Returns:
            Ticker info dictionary or None if failed after all retries
        """
        # First check cache/repository
        ticker_info = self.repository.get_ticker_info(symbol)
        if ticker_info is not None:
            return ticker_info

        # If not cached, fetch from yfinance with retry logic
        for attempt in range(max_retries):
            try:
                ticker = self.client.get_ticker(symbol)
                ticker_info = ticker.info
                # TODO: Cache the result in repository to reduce future API calls
                # self.repository.save_ticker_info(symbol, ticker_info)
                return ticker_info
            except YFRateLimitError:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                    self.logger.warning(
                        f"Rate limit hit for {symbol}. Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                else:
                    self.logger.error(
                        f"Rate limit exceeded for {symbol} after {max_retries} attempts. "
                        "Yahoo Finance API rate limit reached. Please try again later."
                    )
                    return None
            except Exception as e:
                self.logger.error(f"Error fetching ticker info for {symbol}: {str(e)}")
                return None

        return None

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
        """
        Get country information for a ticker symbol.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Country object or None if not found
        """
        ticker_info = self._get_ticker_info_with_retry(symbol)
        if ticker_info is None:
            return None

        try:
            if ticker_info.get("country"):
                return Country(ticker_info["country"])

            if ticker_info.get("region"):
                return Country(ticker_info["region"])
        except (AttributeError, ValueError):
            pass

        return None

    def get_sector_industry(self, symbol: str) -> tuple[Sector, str | None]:
        """
        Get sector and industry information for a ticker symbol.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Tuple of (Sector, industry string or None)
        """
        ticker_info = self._get_ticker_info_with_retry(symbol)
        if ticker_info is None:
            return Sector.UNKNOWN, None

        try:
            sector = Sector(ticker_info.get("sector")) if ticker_info.get("sector") else Sector.UNKNOWN
            industry = ticker_info.get("industry")
            return sector, industry
        except (AttributeError, ValueError):
            return Sector.UNKNOWN, None
