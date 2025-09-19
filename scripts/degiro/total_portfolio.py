"""poetry run python -m scripts.degiro.total_portfolio"""

# IMPORTATIONS
import json

from degiro_connector.trading.models.account import UpdateOption, UpdateRequest

import scripts.degiro.common as common

trading_api = common.connect_to_degiro()

# SETUP REQUEST
update = trading_api.get_update(
    request_list=[
        UpdateRequest(option=UpdateOption.TOTAL_PORTFOLIO, last_updated=0),
    ],
    raw=True,
)

print(json.dumps(update, indent=4))

trading_api.logout()
