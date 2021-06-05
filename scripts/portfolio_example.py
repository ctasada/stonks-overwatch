# IMPORTATIONS
import json
import logging
import degiro_connector.quotecast.helpers.pb_handler as pb_handler
import pandas as pd

# from IPython.display import display
from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.pb.trading_pb2 import Credentials, Update

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
request_list = Update.RequestList()
request_list.values.extend([
    # Update.Request(option=Update.Option.ORDERS, last_updated=0),
    Update.Request(option=Update.Option.PORTFOLIO, last_updated=0),
    Update.Request(option=Update.Option.TOTALPORTFOLIO, last_updated=0),
])

update = trading_api.get_update(request_list=request_list, raw=False)
update_dict = pb_handler.message_to_dict(message=update)

print(json.dumps(update_dict, indent = 4))

# update_dict['portfolio']['values] => 
# {
#     "realizedFxPl": 0.0,
#     "plBase": {
#         "EUR": -4578.18
#     },
#     "todayRealizedProductPl": 0.0,
#     "portfolioValueCorrection": 0.0,
#     "id": "11789747", => Product Id
#     "price": 131.27,  => Product Price
#     "realizedProductPl": -1.13515854,
#     "todayRealizedFxPl": 0.0,
#     "todayPlBase": {
#         "EUR": -4365.51512
#     },
#     "averageFxRate": 0.824365988519866, => Exchange Rate ?
#     "value": 4365.51512, => Total Value ?
#     "size": 40.0, => Number of Stocks
#     "breakEvenPrice": 138.805,
#     "positionType": "PRODUCT"
# },
# 
# update_dict['total_portfolio']['values'] =>
# {
#     "totalDepositWithdrawal": 22000.01, => Deposited Money
#     "degiroCash": 0.0,
#     "todayDepositWithdrawal": 0.0,
#     "flatexCash": 121.56,
#     "cashFundCompensationPending": 0.0,
#     "freeSpaceNew": { => Vrije Ruimte ?
#         "EUR": 121.56,
#         "USD": 25.2
#     },
#     "cashFundCompensationWithdrawn": 1.29,
#     "cashFundCompensation": 0.19,
#     "todayNonProductFees": 0.0,
#     "totalCash": 121.56,  => Cash
#     "cashFundCompensationCurrency": "EUR",
#     "totalNonProductFees": -10.878364599
# }

# for value in update_dict['portfolio']['values']:

result = dict (
    totalCash = update_dict['total_portfolio']['values']['totalCash'],
    totalDepositWithdrawal = update_dict['total_portfolio']['values']['totalDepositWithdrawal'],
)

print(json.dumps(result, indent = 4))