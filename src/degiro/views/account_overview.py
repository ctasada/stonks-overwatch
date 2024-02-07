from django.views import View
from django.shortcuts import render

from degiro.integration.account_overview import AccountOverviewData

import json

class AccountOverview(View):
    def __init__(self):
        self.accountOverview = AccountOverviewData()

    def get(self, request):
        overview = self.accountOverview.get_account_overview()

        # print (json.dumps(overview, indent=2))

        # filteredOverview = []
        # for transaction in overview:
        #     if (transaction['type'] in ['CASH_TRANSACTION'] and transaction['stockSymbol'] is "") or ('Dividend' in transaction['description']):
        #         filteredOverview.append(transaction)

        context = {
            "accountOverview": overview,
        }

        return render(request, 'account_overview.html', context)