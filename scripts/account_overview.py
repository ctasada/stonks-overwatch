# IMPORTATIONS
import common
import json

from datetime import date

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials
from degiro_connector.trading.models.account import OverviewRequest

trading_api = common.connectToDegiro()

# SETUP REQUEST
from_date = date(
    year=2020,
    month=1,
    day=1,
)

request = OverviewRequest(
    from_date=from_date,
    to_date=date.today(),
)

# FETCH DATA
account_overview = trading_api.get_account_overview(
    overview_request=request,
    raw=True,
)

print(json.dumps(account_overview, indent = 4))

# DISPLAY CASH MOVEMENTS
# for cash_movement in account_overview.get('data').get('cashMovements'):
#     if cash_movement['description'] in ['Dividend', 'Dividendbelasting']:
#         for key, value in cash_movement.items():
#             print(key, ' : ', value)

trading_api.logout()