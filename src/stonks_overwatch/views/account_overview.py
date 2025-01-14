from django.shortcuts import render
from django.views import View

from stonks_overwatch.services.degiro.account_overview import AccountOverviewService


class AccountOverview(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.account_overview = AccountOverviewService()

    def get(self, request):
        overview = self.account_overview.get_account_overview()

        context = {
            "account_overview": overview,
        }

        return render(request, "account_overview.html", context)
