from django.views import View
from django.shortcuts import render
import datetime
import pandas as pd

from degiro.models.account_overview import AccountOverviewModel
from degiro.utils.localization import LocalizationUtility

import json

class Dividends(View):

    DATETIME_PATTERN = '%Y-%m-%d %H:%M:%S'

    def __init__(self):
        self.accountOverview = AccountOverviewModel()

    def get(self, request):
        # We don't need to sort the dict, since it's already coming sorted in DESC date order
        dividendsOverview = self.accountOverview.get_dividends()

        dividends = self.get_dividends_calendar(dividendsOverview)

        for transaction in dividendsOverview:
            # Group dividends by month. We may only need the dividend name and amount
            month = self.format_date_to_month(transaction['date'])

            day = self.get_date_day(transaction['date'])
            stock = transaction['stockSymbol']

            monthEntry = dividends.setdefault(month, dict())
            days = monthEntry.setdefault("days", dict())
            dayEntry = days.setdefault(day, dict())
            stockEntry = dayEntry.setdefault(stock, dict())

            stockEntry['stockName'] = transaction['stockName']
            stockEntry['change'] = stockEntry.setdefault('change', 0) + transaction['change']
            stockEntry['currency'] = transaction['currency']
            stockEntry['formatedChange'] = LocalizationUtility.format_money_value(value = stockEntry['change'], currency = transaction['currency'])

            monthEntry.setdefault("dividends", []).append({
                'day': self.get_date_day(transaction['date']),
                'stockName': transaction['stockName'],
                'stockSymbol': transaction['stockSymbol'],
                'formatedChange': transaction['formatedChange']
            })

            # Number of Payouts in the month
            payouts = monthEntry.setdefault("payouts", 0)
            monthEntry["payouts"] = payouts + 1
            # Total payout in the month
            total = monthEntry.setdefault("total", 0)
            monthEntry["total"] = total + transaction['change']
            monthEntry["formatedTotal"] = LocalizationUtility.format_money_value(value = monthEntry['total'], currency = transaction['currency'])

        context = {
            'dividends': dividends
        }
        
        return render(request, 'dividends.html', context)

    def get_dividends_calendar(self, dividendsOverview):
        dividends = dict()
        
        df = pd.DataFrame(dividendsOverview)
        periodStart = min(df['date'])
        periodEnd = datetime.date.today()
        period = pd.period_range(start=periodStart, end=periodEnd, freq='M')[::-1]

        for month in period:
            month = month.strftime('%B %Y')
            monthEntry = dividends.setdefault(month, dict())
            monthEntry.setdefault("payouts", 0)
            monthEntry.setdefault("total", 0)
            monthEntry.setdefault("formatedTotal", LocalizationUtility.format_money_value(value = 0, currencySymbol = LocalizationUtility.get_base_currency_symbol()
))
        return dividends

    def format_date_to_month(self, value: str):
        time = datetime.datetime.strptime(value, self.DATETIME_PATTERN)
        return time.strftime('%B %Y')

    def get_date_day(self, value: str):
        time = datetime.datetime.strptime(value, self.DATETIME_PATTERN)
        return time.strftime('%d')