"""poetry run python -m scripts.degiro.upcoming_payments"""

# IMPORTATIONS
import json

import scripts.degiro.common as common

trading_api = common.connect_to_degiro()

# FETCH AGENDA
payments = trading_api.get_upcoming_payments(raw=True)

print(json.dumps(payments, indent=4))

# {
#     "data": [
#         {
#             "caId": "773063",
#             "product": "Microsoft Corp",
#             "description": "Dividend 0.8300 * 25.00 aandelen",
#             "currency": "USD",
#             "amount": "20.75",
#             "amountInBaseCurr": "18.28",
#             "payDate": "2025-06-12",
#             "ca_id": "773063"
#         },
#         {
#             "caId": "773063",
#             "product": "Microsoft Corp",
#             "description": "Dividendbelasting -0.1244 * 25.00 Aandelen",
#             "currency": "USD",
#             "amount": "-3.11",
#             "amountInBaseCurr": "-2.74",
#             "payDate": "2025-06-12",
#             "ca_id": "773063"
#         },
#     ]
# }
