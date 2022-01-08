# IMPORTATIONS
import json
import logging
import degiro_connector.core.helpers.pb_handler as pb_handler
import pandas as pd

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.trading_pb2 import Credentials, ProductsInfo, Update

# SETUP LOGGING LEVEL
logging.basicConfig(level=logging.DEBUG)

# SETUP CONFIG DICT
with open('../config/config.json') as config_file:
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
request_list = Update.RequestList()
request_list.values.extend([
    Update.Request(option=Update.Option.PORTFOLIO, last_updated=0),
])

update = trading_api.get_update(request_list=request_list, raw=False)
update_dict = pb_handler.message_to_dict(message=update)

products_ids = []

# ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
for portfolio in update_dict['portfolio']['values']:
    # Seems that 'FLATEX_EUR' and 'FLATEX_USD' are returned
    if portfolio['id'].isnumeric():
        products_ids.append(int(portfolio['id']))

# SETUP REQUEST
request = ProductsInfo.Request()
request.products.extend(list(set(products_ids)))

# FETCH DATA
products_info = trading_api.get_products_info(
    request=request,
    raw=True,
)

# DEBUG Values
#print(json.dumps(update_dict, indent = 4))
# print(json.dumps(products_info, indent = 4))

myPortfolio = []

for portfolio in update_dict['portfolio']['values']:
    if portfolio['id'].isnumeric():
        info = products_info['data'][portfolio['id']]
        myPortfolio.append(
            dict(
                name=info['name'],
                symbol = info['symbol'],
                size = portfolio['size'],
                price = portfolio['price'],
                currency = info['currency'],
                breakEvenPrice = portfolio['breakEvenPrice'], # GAK: Average Purchase Price                
                value = portfolio['value'],
                isin = info['isin'],
            )
        )

# print(myPortfolio)

trading_api.logout()