# IMPORTATIONS
import json
import logging

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.trading_pb2 import (
    Credentials,
    ProductsInfo,
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
request = ProductsInfo.Request()
request.products.extend([11789747])

# FETCH DATA
products_info = trading_api.get_products_info(
    request=request,
    raw=True,
)

# DISPLAY PRODUCTS_INFO
print(json.dumps(products_info, indent = 4))

# {
#     "data": {
#         "11789747": {
#             "id": "11789747",
#             "name": "CRISPR Therapeutics AG",
#             "isin": "CH0334081137",
#             "symbol": "CRSP",
#             "contractSize": 1.0,
#             "productType": "STOCK",
#             "productTypeId": 1,
#             "tradable": true,
#             "category": "C",
#             "currency": "USD",
#             "exchangeId": "663",
#             "onlyEodPrices": false,
#             "orderTimeTypes": [
#                 "DAY"
#             ],
#             "buyOrderTypes": [
#                 "LIMIT",
#                 "MARKET",
#                 "STOPLOSS",
#                 "STOPLIMIT"
#             ],
#             "sellOrderTypes": [
#                 "LIMIT",
#                 "MARKET",
#                 "STOPLOSS",
#                 "STOPLIMIT"
#             ],
#             "productBitTypes": [],
#             "closePrice": 131.27,
#             "closePriceDate": "2021-04-30",
#             "feedQuality": "BT",
#             "orderBookDepth": 0,
#             "vwdIdentifierType": "vwdkey",
#             "vwdId": "CRSP.BATS,E",
#             "qualitySwitchable": false,
#             "qualitySwitchFree": false,
#             "vwdModuleId": 31,
#             "feedQualitySecondary": "D15",
#             "orderBookDepthSecondary": 0,
#             "vwdIdentifierTypeSecondary": "issueid",
#             "vwdIdSecondary": "350014346",
#             "qualitySwitchableSecondary": true,
#             "qualitySwitchFreeSecondary": false,
#             "vwdModuleIdSecondary": 21
#         }
#     }
# }