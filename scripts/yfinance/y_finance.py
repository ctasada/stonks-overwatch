"""poetry run python -m scripts.yfinance.y_finance"""

from scripts.common import setup_python_path

setup_python_path()

from stonks_overwatch.services.brokers.yfinance.client.yfinance_client import YFinanceClient  # noqa: E402

client = YFinanceClient(enable_debug=True)

# Can use the Symbol or the ISIN
ticker = client.get_ticker("TNXP")
# print(ticker.info) # Returns information like country, sector and others

# Fetch stock split data
splits = client.get_stock_splits("TNXP")
print(splits)
