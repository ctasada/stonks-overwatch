# IMPORTATIONS
import common
import json

from datetime import date
from degiro_connector.trading.models.transaction import HistoryRequest

trading_api = common.connectToDegiro()

# SETUP REQUEST
from_date = date(
    year=2020,
    month=1,
    day=1,
)

# FETCH DATA
transactions_history = trading_api.get_transactions_history(
    transaction_request=HistoryRequest(
        from_date=from_date,
        to_date=date.today(),
    ),
    raw=True,
)

# DISPLAY TRANSACTIONS
# for transaction in transactions_history.values:
#     print(dict(transaction))

print(json.dumps(transactions_history, indent=4))

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

trading_api.logout()
