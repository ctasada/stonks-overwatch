"""poetry run python -m scripts.degiro.products_config"""

# IMPORTATIONS
import json

import scripts.degiro.common as common

trading_api = common.connect_to_degiro()

# FETCH DATA
products_config = trading_api.get_products_config()

# DISPLAY PRODUCTS_INFO
print(json.dumps(products_config, indent=4))

trading_api.logout()
