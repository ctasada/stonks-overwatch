from datetime import date
from django.views import View
from django.shortcuts import render
from django.db import connection

import pandas as pd

from degiro.integration.portfolio import PortfolioData
from degiro.utils.db_utils import dictfetchall
from degiro.utils.localization import LocalizationUtility

import logging

from scripts.commons import DATE_FORMAT


class Deposits(View):
    logger = logging.getLogger("stocks_portfolio.deposits.views")

    def __init__(self):
        self.portfolio = PortfolioData()

    def get(self, request):
        cash_contributions = self._calculate_cash_contributions()
        deposits = self._get_cash_deposits()
        total_portfolio = self.portfolio.get_portfolio_total()

        context = {
            "total_deposits": total_portfolio['totalDepositWithdrawal'],
            "deposits": deposits,
            "deposit_growth": {"value": cash_contributions},
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

    def _get_cash_deposits(self) -> dict:
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
        df["date"] = pd.to_datetime(df["date"]).dt.strftime(DATE_FORMAT)
        df = df.sort_values(by="date")

        baseCurrencySymbol = LocalizationUtility.get_base_currency_symbol()
        baseCurrency = LocalizationUtility.get_base_currency()

        records = []
        for _, row in df.iterrows():
            records.append(
                {
                    'type': 'Deposit',
                    'date': row['date'],
                    'description': row['description'],
                    'change': LocalizationUtility.format_money_value(
                        value=row['change'],
                        currency=baseCurrency,
                        currencySymbol=baseCurrencySymbol
                    )
                }
            )

        return records
