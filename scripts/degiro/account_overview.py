"""poetry run python ./scripts/degiro//account_overview.py"""

# IMPORTATIONS
import json
from datetime import date, datetime

import common
import polars as pl
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
                        "date": datetime.fromisoformat(cash_movement["date"]).date(),
                        "cash": cash_movement["change"],
                    }
                )
    if cash_movement["type"] in ["FLATEX_CASH_SWEEP"]:
        if "productId" in cash_movement:
            cash_contributions.append(
                {
                    "date": datetime.fromisoformat(cash_movement["date"]).date(),
                    "cash": cash_movement["change"],
                }
            )

# print(json.dumps(cash_contributions, indent = 4))

trading_api.logout()

# Create a polars DataFrame directly from the cash_contributions list
df = pl.DataFrame(cash_contributions)

if len(df) > 0:
    # Sort the DataFrame by the 'date' column
    df = df.sort("date")

    # Group by date and sum cash (in case there are multiple entries for the same date)
    df = df.group_by("date").agg(pl.col("cash").sum())

    # Sort again after grouping
    df = df.sort("date")

    # Calculate cumulative sum for the 'cash' column
    df = df.with_columns(pl.col("cash").cum_sum().alias("cumulative_cash"))

print(df)
