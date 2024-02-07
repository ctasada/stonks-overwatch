from datetime import date
from django.views import View
from django.shortcuts import render
from django.db import connection

import pandas as pd

from degiro.utils.db_utils import dictfetchall
from degiro.integration.portfolio import PortfolioData
from degiro.utils.localization import LocalizationUtility
from degiro_connector.trading.models.account import OverviewRequest
from degiro.utils.degiro import DeGiro

import json

class Dashboard(View):
    def __init__(self):
        self.portfolio = PortfolioData()

    def get(self, request):
        sectorsContext = self._getSectors()
        growthContext = self._getGrowth()

        context = {
            "growth": growthContext,
            "sectors": sectorsContext
        }

        print(context)
        
        # FIXME: Simplify this response
        return render(request, 'dashboard.html', context)

    def _getSectors(self):
        portfolio = self.portfolio.get_portfolio()
        portfolio = sorted(portfolio, key=lambda k: k['sector'])
        # print (json.dumps(portfolio, indent=2))

        sectors = {}

        stockLabels = []
        stockValues = []

        for stock in portfolio:
            if stock['isOpen']:
                sectorName = stock['sector']
                sectors[sectorName] = sectors.get(sectorName, 0) + stock['value']
                stockLabels.append(stock['symbol'])
                stockValues.append(stock['value'])

        sectorLabels = []
        sectorValues = []
        for key in sectors:
            sectorLabels.append(key)
            sectorValues.append(sectors[key])

        return {
                "sectors": {
                    "labels": sectorLabels,
                    "values": sectorValues,
                },
                "stocks": {
                    "labels": stockLabels,
                    "values": stockValues,
                },
                "currencySymbol": LocalizationUtility.get_base_currency_symbol(),
            }
    
    def _getGrowth(self):
        cash_contributions = self._calculate_cash_contributions()

        return {
            "cash_contributions": cash_contributions
        }

    def _calculate_cash_contributions(self) -> dict:
        # FIXME: DeGiro doesn't a consistent description or type. Missing the new value for 'Refund'
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
        df['date'] = pd.to_datetime(df['date']).dt.date
        # Group by day, adding the values
        df.set_index('date', inplace=True)
        df = df.sort_values(by='date')
        df = df.groupby(df.index)['change'].sum().reset_index()
        # Do the cummulative sum
        df['contributed'] = df['change'].cumsum()

        cashContributions = df.to_dict('records')
        for contribution in cashContributions:
            contribution['date'] = contribution['date'].strftime('%Y-%m-%d')

        dataset = []
        for contribution in cashContributions:
            dataset.append({'x': contribution['date'], 'y': contribution['contributed']})

        # Append today with the last value to draw the line properly
        dataset.append({'x': date.today().strftime('%Y-%m-%d'), 'y': cashContributions[-1]['contributed']})

        return dataset
