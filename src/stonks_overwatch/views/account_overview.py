from django.shortcuts import render
from django.views import View

from stonks_overwatch.services.account_overview_aggregator import AccountOverviewAggregatorService
from stonks_overwatch.services.session_manager import SessionManager

class AccountOverview(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.account_overview = AccountOverviewAggregatorService()

    def get(self, request):
        selected_portfolio = SessionManager.get_selected_portfolio(request)
        overview = self.account_overview.get_account_overview(selected_portfolio)

        context = {
            "account_overview": overview,
        }

        return render(request, "account_overview.html", context)
