"""
poetry run python ./scripts/products_info.py
"""
# IMPORTATIONS
import common
import json

trading_api = common.connectToDegiro()

# FETCH DATA
products_info = trading_api.get_products_info(
    product_list=[11789747],
    raw=True,
)

# DISPLAY PRODUCTS_INFO
print(json.dumps(products_info, indent=4))

trading_api.logout()
