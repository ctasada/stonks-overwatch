# IMPORTATIONS
import datetime
import json
import logging

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.pb.trading_pb2 import (
    Credentials,
    TransactionsHistory,
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
today = datetime.date.today()
from_date = TransactionsHistory.Request.Date(
    year=2020,
    month=1,
    day=1,
)
to_date = TransactionsHistory.Request.Date(
    year=today.year,
    month=today.month,
    day=today.day,
)
request = TransactionsHistory.Request(
    from_date=from_date,
    to_date=to_date,
)

# FETCH DATA
transactions_history = trading_api.get_transactions_history(
    request=request,
    raw=True,
)

# DISPLAY TRANSACTIONS
# for transaction in transactions_history.values:
#     print(dict(transaction))

print(json.dumps(transactions_history, indent = 4))

# {
#     "data": [
#         {
#             "id": 188561689,
#             "productId": 322171,
#             "date": "2020-03-11T14:30:00+01:00",
#             "buysell": "B",
#             "price": 52.39,
#             "quantity": 20,
#             "total": -1047.8,
#             "orderTypeId": 0,
#             "counterParty": "MK",
#             "transfered": false,
#             "fxRate": 1.1326,
#             "totalInBaseCurrency": -924.2303783661,
#             "feeInBaseCurrency": -0.57,
#             "totalPlusFeeInBaseCurrency": -924.8003783661,
#             "transactionTypeId": 0,
#             "tradingVenue": "XNAS"
#         },
# }