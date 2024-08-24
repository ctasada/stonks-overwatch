"""
poetry run python ./scripts/account_info.py
"""
# IMPORTATIONS
import json
import common

trading_api = common.connectToDegiro()
account_info = trading_api.get_account_info()
trading_api.logout()

print(json.dumps(account_info, indent=4))
