"""poetry run python ./scripts/transactions.py"""

# IMPORTATIONS
import json
from datetime import date

import common
from degiro_connector.trading.models.transaction import HistoryRequest

trading_api = common.connect_to_degiro()

# SETUP REQUEST
from_date = date(
    year=2020,
    month=1,
    day=1,
)

# FETCH TRANSACTIONS DATA
transactions_history = trading_api.get_transactions_history(
    transaction_request=HistoryRequest(
        from_date=from_date,
        to_date=date.today(),
    ),
    raw=True,
)

print(json.dumps(transactions_history, indent=4))

products_ids = []

# ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
for transaction in transactions_history["data"]:
    products_ids.append(int(transaction["productId"]))

products_ids = list(set(products_ids))

# FETCH DATA
products_info = trading_api.get_products_info(
    product_list=products_ids,
    raw=True,
)

# DISPLAY PRODUCTS_INFO
print(json.dumps(products_info, indent=4))

trading_api.logout()
