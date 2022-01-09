# IMPORTATIONS
import datetime
import json
import logging

import degiro_connector.core.helpers.pb_handler as pb_handler
from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.trading_pb2 import (
    Update,
    Credentials,
)

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
request_list = Update.RequestList()
request_list.values.extend([
    Update.Request(option=Update.Option.TOTALPORTFOLIO, last_updated=0),
])

update = trading_api.get_update(request_list=request_list)
update_dict = pb_handler.message_to_dict(message=update)
# total_portfolio_df = pd.DataFrame(update_dict['total_portfolio']['values'])

print(json.dumps(update_dict, indent = 4))

# DISPLAY CASH MOVEMENTS
# for cash_movement in account_overview.values['cashMovements']:
    # print('date:', cash_movement['date'])
    # print('valueDate:', cash_movement['valueDate'])
    # print('productId:', dict(cash_movement).get('productId', 'unknown'))
    # print('currency:', dict(cash_movement).get('currency', 'unknown'))
    # print('change:', dict(cash_movement).get('change', 'unknown'))
    # print(cash_movement)
    # break