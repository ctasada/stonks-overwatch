# IMPORTATIONS
import common
import json

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials
from degiro_connector.trading.models.product import ProductInfo

trading_api = common.connectToDegiro()

# FETCH DATA
products_info = trading_api.get_products_info(
    product_list=[11789747],
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

trading_api.logout()