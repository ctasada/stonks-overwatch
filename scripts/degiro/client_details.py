"""poetry run python -m scripts.degiro.client_details"""

# IMPORTATIONS
import json

import scripts.degiro.common as common

trading_api = common.connect_to_degiro()

# FETCH CONFIG TABLE
client_details_table = trading_api.get_client_details()
client_details_pretty = json.dumps(
    client_details_table,
    sort_keys=True,
    indent=4,
)

print(client_details_pretty)

trading_api.logout()
