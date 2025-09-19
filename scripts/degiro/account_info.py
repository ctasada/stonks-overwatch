"""poetry run python -m scripts.degiro.account_info"""

# IMPORTATIONS
import json

import scripts.degiro.common as common

trading_api = common.connect_to_degiro()
account_info = trading_api.get_account_info()
trading_api.logout()

print(json.dumps(account_info, indent=4))
