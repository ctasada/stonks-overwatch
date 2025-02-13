from dataclasses import dataclass
from datetime import datetime
from typing import List

import yfinance as yf


@dataclass
class StockSplit:
    date: datetime
    split_ratio: float

def get_stock_splits(ticker: str) -> List[StockSplit]:
    """Get stock splits for a given ticker

    Args:
        ticker (str): Stock ticker. Symbol or ISIN

    Returns:
        List[Dict[str, str]]: List of stock splits
    """
    ticker = yf.Ticker(ticker)
    splits = ticker.splits
    splits_list = [StockSplit(date.to_pydatetime().astimezone(), ratio) for date, ratio in splits.to_dict().items()]
    return splits_list
