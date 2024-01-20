# IMPORTATIONS
import datetime
import json
import logging

from datetime import date
from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials
from degiro_connector.trading.models.product import ProductInfo
from degiro_connector.trading.models.transaction import HistoryRequest

# SETUP LOGGING LEVEL
logging.basicConfig(level=logging.DEBUG)

# SETUP CONFIG DICT
with open('./config/config.json') as config_file:
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
from_date = date(
    year=2020,
    month=1,
    day=1,
)
to_date = date(
    year=today.year,
    month=today.month,
    day=today.day,
)

# FETCH TRANSACTIONS DATA
transactions_history = trading_api.get_transactions_history(
    transaction_request=HistoryRequest(
        from_date=from_date,
        to_date=to_date,
    ),
    raw=True,
)

print(json.dumps(transactions_history, indent = 4))

products_ids = []

# ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
for transaction in transactions_history['data']:
    products_ids.append(int(transaction['productId']))

products_ids = list(set(products_ids))

# FETCH DATA
products_info = trading_api.get_products_info(
    product_list=products_ids,
    raw=True,
)

# DISPLAY PRODUCTS_INFO
print(json.dumps(products_info, indent = 4))
