from django.shortcuts import render
from django.views import View

from degiro.services.account_overview import AccountOverviewService


class AccountOverview(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.account_overview = AccountOverviewService()

    def get(self, request):
        overview = self.account_overview.get_account_overview()

        context = {
            "accountOverview": overview,
        }

        return render(request, "account_overview.html", context)
