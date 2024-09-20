from django.shortcuts import render
from django.views import View

from degiro.services.account_overview import AccountOverviewService


class AccountOverview(View):
    def __init__(self):
        self.accountOverview = AccountOverviewService()

    def get(self, request):
        overview = self.accountOverview.get_account_overview()

        context = {
            "accountOverview": overview,
        }

        return render(request, "account_overview.html", context)
