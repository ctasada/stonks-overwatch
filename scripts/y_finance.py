"""poetry run python ./scripts/y_finance.py"""

import yfinance as yf

# Can use the Symbol or the ISIN
ticker = yf.Ticker('NVDA')
# print(ticker.info) # Returns information like country, sector and others

# Fetch stock split data
splits = ticker.splits
splits_list = [{"date": date.to_pydatetime().astimezone(), "split_ratio": ratio}
               for date, ratio in splits.to_dict().items()]
print(splits_list)
