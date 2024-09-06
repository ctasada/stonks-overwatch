from datetime import date

import pandas as pd
from django.db import connection

from degiro.repositories.cash_movements_repository import CashMovementsRepository
from degiro.utils.db_utils import dictfetchall
from degiro.utils.localization import LocalizationUtility


# FIXME: If data cannot be found in the DB, the code should get it from DeGiro, updating the DB
class DepositsData:
    def __init__(self):
        self.cash_movements_repository = CashMovementsRepository()

    def get_cash_deposits(self) -> dict:
        df = pd.DataFrame(self.cash_movements_repository.get_cash_deposits_raw())

        # Remove hours and keep only the day
        df["date"] = pd.to_datetime(df["date"]).dt.strftime(LocalizationUtility.DATE_FORMAT)
        df = df.sort_values(by="date", ascending=False)

        base_currency_symbol = LocalizationUtility.get_base_currency_symbol()
        base_currency = LocalizationUtility.get_base_currency()

        records = []
        for _, row in df.iterrows():
            records.append(
                {
                    "type": "Deposit" if row["change"] > 0 else "Withdrawal",
                    "date": row["date"],
                    "description": row["description"],
                    "change": row["change"],
                    "changeFormatted": LocalizationUtility.format_money_value(
                        value=row["change"], currency=base_currency, currency_symbol=base_currency_symbol
                    ),
                }
            )

        return records

    def cash_deposits_history(self) -> dict:
        cash_contributions = self.cash_movements_repository.get_cash_deposits_raw()
        df = pd.DataFrame.from_dict(cash_contributions)
        # Remove hours and keep only the day
        df["date"] = pd.to_datetime(df["date"]).dt.date
        # Group by day, adding the values
        df.set_index("date", inplace=True)
        df = df.sort_values(by="date")
        df = df.groupby(df.index)["change"].sum().reset_index()
        # Do the cummulative sum
        df["contributed"] = df["change"].cumsum()

        cash_contributions = df.to_dict("records")
        for contribution in cash_contributions:
            contribution["date"] = contribution["date"].strftime(LocalizationUtility.DATE_FORMAT)

        dataset = []
        for contribution in cash_contributions:
            dataset.append(
                {
                    "date": contribution["date"],
                    "total_deposit": LocalizationUtility.round_value(contribution["contributed"]),
                }
            )

        # Append today with the last value to draw the line properly
        dataset.append(
            {
                "date": LocalizationUtility.format_date_from_date(date.today()),
                "total_deposit": cash_contributions[-1]["contributed"],
            }
        )

        return dataset

    def calculate_cash_account_value(self) -> dict:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT date, balance_total
                FROM degiro_cashmovements
                WHERE currency = 'EUR'
                    AND type = 'CASH_TRANSACTION'
                """
            )
            cash_contributions = dictfetchall(cursor)

        # Create DataFrame from the fetched data
        df = pd.DataFrame.from_dict(cash_contributions)

        # Convert the 'date' column to datetime and remove the time component
        df["date"] = pd.to_datetime(df["date"]).dt.normalize()

        # Group by date and take the last balance_total for each day
        df = df.groupby("date", as_index=False).last()

        # Sort values by date (just in case)
        df = df.sort_values(by="date")

        # Set the 'date' column as the index and fill missing dates
        df.set_index("date", inplace=True)
        df = df.resample("D").ffill()

        # Convert the DataFrame to a dictionary with date as the key (converted to string)
        # and balance_total as the value
        dataset = {date.strftime("%Y-%m-%d"): float(balance) for date, balance in df["balanceTotal"].items()}

        return dataset
