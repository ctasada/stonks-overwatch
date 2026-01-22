import os
from dataclasses import dataclass
from datetime import datetime
from typing import List

import yfinance as yf
from yfinance import Ticker

import stonks_overwatch.settings
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.core.singleton import singleton


@dataclass
class StockSplit:
    date: datetime
    split_ratio: float

    def to_dict(self) -> dict:
        return {"date": self.date.isoformat(), "split_ratio": self.split_ratio}

    @classmethod
    def from_dict(cls, split):
        return cls(date=datetime.fromisoformat(split["date"]), split_ratio=split["split_ratio"])


@singleton
class YFinanceClient:
    logger = StonksLogger.get_logger("stonks_overwatch.yfinance_client", "[YFINANCE|CLIENT]")

    cache_path = os.path.join(stonks_overwatch.settings.STONKS_OVERWATCH_CACHE_DIR, "yfinance.cache")

    def __init__(self, enable_debug: bool = False):
        if enable_debug:
            yf.config.debug.logging = True

    def __convert_to_ticker(self, ticker: Ticker | str) -> Ticker:
        if isinstance(ticker, str):
            return self.get_ticker(ticker)

        return ticker

    def get_ticker(self, ticker: str) -> Ticker:
        self.logger.debug(f"Get Ticker for {ticker}")
        return yf.Ticker(ticker)

    def get_stock_splits(self, ticker: Ticker | str) -> List[StockSplit]:
        """Get stock splits for a given ticker

        Args:
            ticker (str): Stock ticker. Symbol or ISIN

        Returns:
            List[StockSplit]: List of stock splits
        """
        self.logger.debug(f"Get Stock Splits for {ticker.ticker if isinstance(ticker, Ticker) else ticker}")

        ticker_info = self.__convert_to_ticker(ticker)
        if ticker_info is None:
            return []

        splits = ticker_info.splits
        splits_list = [StockSplit(date.to_pydatetime().astimezone(), ratio) for date, ratio in splits.to_dict().items()]
        return splits_list
