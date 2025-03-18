import os
from dataclasses import dataclass
from datetime import datetime
from typing import List

import requests_cache
import yfinance as yf
from requests_cache import CachedSession
from yfinance import Ticker

import settings
from stonks_overwatch.services.models import Country
from stonks_overwatch.utils.constants import Sector

@dataclass
class StockSplit:
    date: datetime
    split_ratio: float

def __yfinance_cache() -> CachedSession:
    cache_path = os.path.join(settings.TEMP_DIR, 'yfinance.cache')
    return requests_cache.CachedSession(cache_path)

def __get_ticker_info(ticker: str) -> Ticker:
    return yf.Ticker(ticker, session=__yfinance_cache())

def get_stock_splits(ticker: str) -> List[StockSplit]:
    """Get stock splits for a given ticker

    Args:
        ticker (str): Stock ticker. Symbol or ISIN

    Returns:
        List[Dict[str, str]]: List of stock splits
    """
    ticker = __get_ticker_info(ticker)
    splits = ticker.splits
    splits_list = [StockSplit(date.to_pydatetime().astimezone(), ratio) for date, ratio in splits.to_dict().items()]
    return splits_list

def get_country(ticker: str) -> Country | None:
    ticker = __get_ticker_info(ticker)

    try:
        if ticker.info.get('country'):
            return Country(ticker.info['country'])

        if ticker.info.get('region'):
            return Country(ticker.info['region'])
    except AttributeError:
        pass

    return None

def get_sector_industry(ticker: str) -> tuple[Sector, str | None]:
    ticker = __get_ticker_info(ticker)

    try:
        sector = Sector(ticker.info.get('sector')) if ticker.info.get('sector') else Sector.UNKNOWN
        industry = ticker.info.get('industry')
        return sector, industry
    except AttributeError:
        return Sector.UNKNOWN, None
