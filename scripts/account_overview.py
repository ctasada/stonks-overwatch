"""poetry run python ./scripts/account_overview.py
"""

# IMPORTATIONS
import json
from datetime import date

import common
import pandas as pd
from degiro_connector.trading.models.account import OverviewRequest

trading_api = common.connect_to_degiro()

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

print(json.dumps(account_overview, indent=4))

cash_contributions = []

# DISPLAY CASH MOVEMENTS
# FIXME: Money from Dividends is not yet included.
# print(json.dumps(account_overview.get('data').get('cashMovements'), indent = 4))
for cash_movement in account_overview.get("data").get("cashMovements"):
    if cash_movement["type"] in ["CASH_TRANSACTION"]:
        if "productId" not in cash_movement:
            if cash_movement["currency"] == "EUR":
                cash_contributions.append(
                    {
                        "date": pd.to_datetime(cash_movement["date"]).to_period("D"),
                        "cash": cash_movement["change"],
                    }
                )
    if cash_movement["type"] in ["FLATEX_CASH_SWEEP"]:
        if "productId" in cash_movement:
            cash_contributions.append(
                {
                    "date": pd.to_datetime(cash_movement["date"]).to_period("D"),
                    "cash": cash_movement["change"],
                }
            )

# print(json.dumps(cash_contributions, indent = 4))

trading_api.logout()

df = pd.DataFrame(columns=["date", "cash"])

# create a DataFrame
df = pd.concat([df, pd.DataFrame(cash_contributions)], ignore_index=True)

# Set the index explicitly
df.set_index("date", inplace=True)

# Sort the DataFrame by the 'date' column
df = df.sort_values(by="date")

# Convert the index to datetime.date and group by day
result = df.groupby(df.index)["cash"].sum().reset_index()

# Calculate cumulative sum for the 'cash' column
df["cumulative_cash"] = df["cash"].cumsum()

print(df)
