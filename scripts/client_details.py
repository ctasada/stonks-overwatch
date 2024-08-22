"""
poetry run python ./scripts/client_details.py
"""
# IMPORTATIONS
import common
import json


trading_api = common.connectToDegiro()

# FETCH CONFIG TABLE
client_details_table = trading_api.get_client_details()
client_details_pretty = json.dumps(
    client_details_table,
    sort_keys=True,
    indent=4,
)

print(client_details_pretty)

trading_api.logout()
