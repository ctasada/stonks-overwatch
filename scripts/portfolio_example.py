# IMPORTATIONS
import json
import logging
import pandas as pd

# from IPython.display import display
from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials
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
    # Update.Request(option=Update.Option.ORDERS, last_updated=0),
    UpdateRequest(option=UpdateOption.PORTFOLIO, last_updated=0),
    UpdateRequest(option=UpdateOption.TOTAL_PORTFOLIO, last_updated=0),
], raw=False)

# print(update)
# print(json.dumps(update, indent = 4))

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
    totalCash = update['totalPortfolio']['value']['totalCash'],
    totalDepositWithdrawal = update['totalPortfolio']['value']['totalDepositWithdrawal'],
)

print(json.dumps(result, indent = 4))