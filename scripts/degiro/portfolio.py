"""poetry run python -m scripts.degiro.portfolio"""

# IMPORTATIONS
import json

from degiro_connector.trading.models.account import UpdateOption, UpdateRequest

import scripts.degiro.common as common

trading_api = common.connect_to_degiro()

# SETUP REQUEST
update = trading_api.get_update(
    request_list=[
        UpdateRequest(option=UpdateOption.PORTFOLIO, last_updated=0),
    ],
    raw=True,
)

# print(json.dumps(update, indent=4))

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
# print(json.dumps(products_info, indent=4))

my_portfolio = []

for portfolio in update["portfolio"]["value"]:
    if portfolio["id"].isnumeric():
        info = products_info["data"][portfolio["id"]]
        size_value = next((item["value"] for item in portfolio["value"] if item["name"] == "size"), None)
        price_value = next((item["value"] for item in portfolio["value"] if item["name"] == "price"), None)
        break_even_price_value = next(
            (item["value"] for item in portfolio["value"] if item["name"] == "breakEvenPrice"), None
        )
        value_value = next((item["value"] for item in portfolio["value"] if item["name"] == "value"), None)
        my_portfolio.append(
            {
                "name": info["name"],
                "symbol": info["symbol"],
                "size": size_value,
                "price": price_value,
                "currency": info["currency"],
                "breakEvenPrice": break_even_price_value,  # GAK: Average Purchase Price
                "value": value_value,
                "isin": info["isin"],
            }
        )

print(json.dumps(my_portfolio, indent=4))

trading_api.logout()
