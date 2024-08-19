from datetime import date
from django.views import View
from django.shortcuts import render
from django.db import connection

import pandas as pd

from degiro.utils.db_utils import dictfetchall
from degiro.utils.localization import LocalizationUtility

from currency_converter import CurrencyConverter

import logging


class Deposits(View):
    logger = logging.getLogger("stocks_portfolio.dashboard.views")
    currencyConverter = CurrencyConverter(
        fallback_on_missing_rate=True, fallback_on_wrong_date=True
    )

    def get(self, request):
        cash_contributions = self._calculate_cash_contributions()

        context = {
            "deposits": {"value": cash_contributions},
        }

        return render(request, "deposits.html", context)

    def _calculate_cash_contributions(self) -> dict:
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
            contribution["date"] = contribution["date"].strftime("%Y-%m-%d")

        dataset = []
        for contribution in cashContributions:
            dataset.append(
                {
                    "x": contribution["date"],
                    "y": LocalizationUtility.round_value(contribution["contributed"]),
                }
            )

        # Append today with the last value to draw the line properly
        dataset.append(
            {
                "x": date.today().strftime("%Y-%m-%d"),
                "y": cashContributions[-1]["contributed"],
            }
        )

        return dataset

    def _calculate_cash_account_value(self) -> dict:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT date, balance_total
                FROM degiro_cashmovements
                WHERE currency = 'EUR'
                    AND type = 'CASH_TRANSACTION'
                """
            )
            cashContributions = dictfetchall(cursor)

        # Create DataFrame from the fetched data
        df = pd.DataFrame.from_dict(cashContributions)

        # Convert the 'date' column to datetime and remove the time component
        df["date"] = pd.to_datetime(df["date"]).dt.normalize()

        # Group by date and take the last balance_total for each day
        df = df.groupby("date", as_index=False).last()

        # Sort values by date (just in case)
        df = df.sort_values(by="date")

        # Set the 'date' column as the index and fill missing dates
        df.set_index("date", inplace=True)
        df = df.resample("D").ffill()

        # Convert the DataFrame to a dictionary with date as the key (converted to string) and balance_total as the value
        dataset = {
            date.strftime("%Y-%m-%d"): float(balance)
            for date, balance in df["balance_total"].items()
        }

        return dataset
