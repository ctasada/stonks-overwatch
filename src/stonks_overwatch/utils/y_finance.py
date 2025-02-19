from dataclasses import dataclass
from datetime import datetime
from typing import List

import requests_cache
import yfinance as yf
from requests_cache import CachedSession


@dataclass
class StockSplit:
    date: datetime
    split_ratio: float

def __yfinance_cache() -> CachedSession:
    return requests_cache.CachedSession('yfinance.cache')


def get_stock_splits(ticker: str) -> List[StockSplit]:
    """Get stock splits for a given ticker

    Args:
        ticker (str): Stock ticker. Symbol or ISIN

    Returns:
        List[Dict[str, str]]: List of stock splits
    """
    ticker = yf.Ticker(ticker, session=__yfinance_cache())
    splits = ticker.splits
    splits_list = [StockSplit(date.to_pydatetime().astimezone(), ratio) for date, ratio in splits.to_dict().items()]
    return splits_list
