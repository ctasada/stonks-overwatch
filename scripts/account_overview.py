# IMPORTATIONS
import datetime
import json
import logging

from datetime import date

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials
from degiro_connector.trading.models.account import OverviewRequest

# SETUP LOGGING LEVEL
logging.basicConfig(level=logging.DEBUG)

# SETUP CONFIG DICT
with open('./config/config.json') as config_file:
    config_dict = json.load(config_file)

# SETUP CREDENTIALS
int_account = config_dict['int_account']
username = config_dict['username']
password = config_dict['password']
totp_secret_key = config_dict['totp_secret_key']
credentials = Credentials(
    int_account=int_account,
    username=username,
    password=password,
    totp_secret_key=totp_secret_key,
)

# SETUP TRADING API
trading_api = TradingAPI(credentials=credentials)

# CONNECT
trading_api.connect()

# SETUP REQUEST
today = datetime.date.today()
from_date = date(
    year=2020,
    month=1,
    day=1,
)
to_date = date(
    year=today.year,
    month=today.month,
    day=today.day,
)
request = OverviewRequest(
    from_date=from_date,
    to_date=to_date,
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
