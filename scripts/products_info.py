"""
poetry run python ./scripts/products_info.py
"""
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

trading_api.logout()
