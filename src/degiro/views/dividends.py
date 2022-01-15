from django.views import View
from django.shortcuts import render
import datetime

from degiro.models.account_overview import AccountOverviewModel
from degiro.utils.localization import LocalizationUtility

import json

class Dividends(View):
    def __init__(self):
        self.accountOverview = AccountOverviewModel()

    def get(self, request):
        # We don't need to sort the dict, since it's already coming sorted in DESC date order
        dividendsOverview = self.accountOverview.get_dividends()

        dividends = dict()
        for transaction in dividendsOverview:
            # Group dividends by month. We may only need the dividend name and amount
            month = self.format_date_to_month(transaction['date'])

            entry = dividends.setdefault(month, dict())
            entry.setdefault("dividends", []).append({
                'day': self.get_date_day(transaction['date']),
                'stockName': transaction['stockName'],
                'stockSymbol': transaction['stockSymbol'],
                'unsettleCash': transaction['formatedUnsettledCash']
            })
            # Number of Payouts in the month
            payouts = entry.setdefault("payouts", 0)
            entry["payouts"] = payouts + 1
            # Total payout in the month
            total = entry.setdefault("total", 0)
            entry["total"] = total + transaction['unsettledCash']

        context = {
            'dividends': dividends
        }
        
        return render(request, 'dividends.html', context)

    def format_date_to_month(self, value: str):
        time = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        return time.strftime('%B %Y')

    def get_date_day(self, value: str):
        time = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        return time.strftime('%d')