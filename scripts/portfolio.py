# IMPORTATIONS
import json
import logging
import pandas as pd

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials
from degiro_connector.trading.models.product import ProductInfo
from degiro_connector.trading.models.account import UpdateOption, UpdateRequest

# SETUP LOGGING LEVEL
logging.basicConfig(level=logging.DEBUG)

# SETUP CONFIG DICT
with open('./config/config.json') as config_file:
    config = json.load(config_file)

# SETUP CREDENTIALS
int_account = config['int_account']
username = config['username']
password = config['password']
totp_secret_key = config['totp_secret_key']

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
update = trading_api.get_update(request_list=[
    UpdateRequest(option=UpdateOption.PORTFOLIO, last_updated=0),
], raw=True)

products_ids = []

# ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
for portfolio in update['portfolio']['value']:
    # Seems that 'FLATEX_EUR' and 'FLATEX_USD' are returned
    if portfolio['id'].isnumeric():
        products_ids.append(int(portfolio['id']))

# FETCH DATA
products_info = trading_api.get_products_info(
    product_list=list(set(products_ids)),
    raw=True,
)

# DEBUG Values
#print(json.dumps(update_dict, indent = 4))
print(json.dumps(products_info, indent = 4))

myPortfolio = []

for portfolio in update['portfolio']['value']:
    if portfolio['id'].isnumeric():
        info = products_info['data'][portfolio['id']]
        myPortfolio.append(
            dict(
                name=info['name'],
                symbol = info['symbol'],
                # size = portfolio['size'],
                # price = portfolio['closePrice'],
                currency = info['currency'],
                # breakEvenPrice = portfolio['breakEvenPrice'], # GAK: Average Purchase Price                
                # value = portfolio['value'],
                isin = info['isin'],
            )
        )

# print(myPortfolio)

trading_api.logout()