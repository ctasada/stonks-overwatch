from datetime import date
from django.db import connection
from degiro.utils.db_utils import dictfetchall
from degiro.utils.localization import LocalizationUtility
import pandas as pd


class DepositsData:

    def get_cash_deposits(self) -> dict:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT date, description, change
                FROM degiro_cashmovements
                WHERE currency = 'EUR'
                    AND description IN ('iDEAL storting', 'iDEAL Deposit', 'Terugstorting')
                """
            )
            df = pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])

        # Remove hours and keep only the day
        df["date"] = pd.to_datetime(df["date"]).dt.strftime(LocalizationUtility.DATE_FORMAT)
        df = df.sort_values(by="date", ascending=False)

        baseCurrencySymbol = LocalizationUtility.get_base_currency_symbol()
        baseCurrency = LocalizationUtility.get_base_currency()

        records = []
        for _, row in df.iterrows():
            records.append(
                {
                    'type': 'Deposit' if row['change'] > 0 else 'Withdrawal',
                    'date': row['date'],
                    'description': row['description'],
                    'change': row['change'],
                    'changeFormatted': LocalizationUtility.format_money_value(
                        value=row['change'],
                        currency=baseCurrency,
                        currencySymbol=baseCurrencySymbol
                    )
                }
            )

        return records

    def cash_deposits_history(self) -> dict:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT date, description, change
                FROM degiro_cashmovements
                WHERE currency = 'EUR'
                    AND description IN ('iDEAL storting', 'iDEAL Deposit', 'Terugstorting')
                """
            )
            cashContributions = dictfetchall(cursor)

        df = pd.DataFrame.from_dict(cashContributions)
        # Remove hours and keep only the day
        df["date"] = pd.to_datetime(df["date"]).dt.date
        # Group by day, adding the values
        df.set_index("date", inplace=True)
        df = df.sort_values(by="date")
        df = df.groupby(df.index)["change"].sum().reset_index()
        # Do the cummulative sum
        df["contributed"] = df["change"].cumsum()

        cashContributions = df.to_dict("records")
        for contribution in cashContributions:
            contribution["date"] = contribution["date"].strftime(LocalizationUtility.DATE_FORMAT)

        dataset = []
        for contribution in cashContributions:
            dataset.append(
                {
                    "date": contribution["date"],
                    "total_deposit": LocalizationUtility.round_value(contribution["contributed"]),
                }
            )

        # Append today with the last value to draw the line properly
        dataset.append(
            {
                "date": date.today().strftime(LocalizationUtility.DATE_FORMAT),
                "total_deposit": cashContributions[-1]["contributed"],
            }
        )

        return dataset
