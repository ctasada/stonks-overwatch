# IMPORTATIONS
import common
import json
from degiro_connector.trading.models.account import UpdateOption, UpdateRequest

trading_api = common.connectToDegiro()

# SETUP REQUEST
update = trading_api.get_update(
    request_list=[
        UpdateRequest(option=UpdateOption.TOTAL_PORTFOLIO, last_updated=0),
    ],
    raw=True,
)

print(json.dumps(update, indent=4))

trading_api.logout()
