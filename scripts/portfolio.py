"""poetry run python ./scripts/portfolio.py
"""

# IMPORTATIONS
import json

import common
from degiro_connector.trading.models.account import UpdateOption, UpdateRequest

trading_api = common.connect_to_degiro()

# SETUP REQUEST
update = trading_api.get_update(
    request_list=[
        UpdateRequest(option=UpdateOption.PORTFOLIO, last_updated=0),
    ],
    raw=True,
)

products_ids = []

# ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
for portfolio in update["portfolio"]["value"]:
    # Seems that 'FLATEX_EUR' and 'FLATEX_USD' are returned
    if portfolio["id"].isnumeric():
        products_ids.append(int(portfolio["id"]))

# FETCH DATA
products_info = trading_api.get_products_info(
    product_list=list(set(products_ids)),
    raw=True,
)

# DEBUG Values
print(json.dumps(products_info, indent=4))

my_portfolio = []

for portfolio in update["portfolio"]["value"]:
    if portfolio["id"].isnumeric():
        info = products_info["data"][portfolio["id"]]
        my_portfolio.append(
            {
                "name": info["name"],
                "symbol": info["symbol"],
                # size = portfolio['size'],
                # price = portfolio['closePrice'],
                "currency": info["currency"],
                # breakEvenPrice = portfolio['breakEvenPrice'], # GAK: Average Purchase Price
                # value = portfolio['value'],
                "isin": info["isin"],
            }
        )

# print(myPortfolio)

trading_api.logout()
