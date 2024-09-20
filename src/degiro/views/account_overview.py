from django.shortcuts import render
from django.views import View

from degiro.repositories.cash_movements_repository import CashMovementsRepository
from degiro.repositories.product_info_repository import ProductInfoRepository
from degiro.services.account_overview import AccountOverviewService


class AccountOverview(View):
    def __init__(self):
        self.cash_movements_repository = CashMovementsRepository()
        self.product_info_repository = ProductInfoRepository()

        self.account_overview = AccountOverviewService(
            cash_movements_repository=self.cash_movements_repository,
            product_info_repository=self.product_info_repository,
        )

    def get(self, request):
        overview = self.account_overview.get_account_overview()

        context = {
            "accountOverview": overview,
        }

        return render(request, "account_overview.html", context)
