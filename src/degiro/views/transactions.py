from django.shortcuts import render
from django.views import View

from degiro.services.transactions import TransactionsService


class Transactions(View):
    def __init__(self):
        self.transactions = TransactionsService()

    def get(self, request):
        transactions = self.transactions.get_transactions()

        context = {
            "transactions": transactions,
        }

        return render(request, "transactions.html", context)
