from django.views import View
from django.shortcuts import render

from degiro.integration.account_overview import AccountOverviewData


class AccountOverview(View):
    def __init__(self):
        self.accountOverview = AccountOverviewData()

    def get(self, request):
        overview = self.accountOverview.get_account_overview()

        context = {
            "accountOverview": overview,
        }

        return render(request, 'account_overview.html', context)
