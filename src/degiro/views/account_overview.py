from django.http import HttpResponse
from django.http import JsonResponse
from django.views import View
from django.shortcuts import render

from degiro.models.account_overview import AccountOverviewModel

import json

class AccountOverview(View):
    def __init__(self):
        self.accountOverview = AccountOverviewModel()

    def get(self, request):
        overview = self.accountOverview.get_account_overview()

        # print (json.dumps(transactions, indent=2))

        context = {
            "accountOverview": overview,
        }

        return render(request, 'account_overview.html', context)
