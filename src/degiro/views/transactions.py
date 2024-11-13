from django.shortcuts import render
from django.views import View

from degiro.services.degiro_service import DeGiroService
from degiro.services.transactions import TransactionsService


class Transactions(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.degiro_service = DeGiroService()
        self.transactions = TransactionsService(
            degiro_service=self.degiro_service,
        )

    def get(self, request):
        transactions = self.transactions.get_transactions()

        context = {
            "transactions": transactions,
        }

        return render(request, "transactions.html", context)
