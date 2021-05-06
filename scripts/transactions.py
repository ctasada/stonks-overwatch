# IMPORTATIONS
import datetime
import json
import logging

from trading.api import API as TradingAPI
from trading.pb.trading_pb2 import (
    Credentials,
    ProductsInfo,
    TransactionsHistory,
)

# SETUP LOGGING LEVEL
logging.basicConfig(level=logging.DEBUG)

# SETUP CONFIG DICT
with open('../config/config.json') as config_file:
    config_dict = json.load(config_file)

# SETUP CREDENTIALS
int_account = config_dict['int_account']
username = config_dict['username']
password = config_dict['password']
totp_secret_key = config_dict['totp_secret_key']
credentials = Credentials(
    int_account=int_account,
    username=username,
    password=password,
    totp_secret_key=totp_secret_key,
)

# SETUP TRADING API
trading_api = TradingAPI(credentials=credentials)

# CONNECT
trading_api.connect()

# SETUP REQUEST
today = datetime.date.today()
from_date = TransactionsHistory.Request.Date(
    year=2020,
    month=1,
    day=1,
)
to_date = TransactionsHistory.Request.Date(
    year=today.year,
    month=today.month,
    day=today.day,
)
request = TransactionsHistory.Request(
    from_date=from_date,
    to_date=to_date,
)

# FETCH TRANSACTIONS DATA
transactions_history = trading_api.get_transactions_history(
    request=request,
    raw=False,
)

products_ids = []

# ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
for transaction in transactions_history.values:
    products_ids.append(int(transaction['productId']))

products_ids = list(set(products_ids))

# SETUP REQUEST
request = ProductsInfo.Request()
request.products.extend(products_ids)

# FETCH DATA
products_info = trading_api.get_products_info(
    request=request,
    raw=True,
)

# DISPLAY PRODUCTS_INFO
print(json.dumps(products_info, indent = 4))
