"""poetry run python ./scripts/yfinance/y_finance.py"""

from stonks_overwatch.services.yfinance.y_finance_client import YFinanceClient

client = YFinanceClient(enable_debug = True)

# Can use the Symbol or the ISIN
ticker = client.get_ticker('TNXP')
# print(ticker.info) # Returns information like country, sector and others

# Fetch stock split data
splits = client.get_stock_splits('TNXP')
print(splits)
