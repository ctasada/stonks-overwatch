from django.shortcuts import render
from django.views import View

from degiro.data.transactions import TransactionsData


class Transactions(View):
    def __init__(self):
        self.transactions = TransactionsData()

    def get(self, request):
        transactions = self.transactions.get_transactions()

        context = {
            "transactions": transactions,
        }

        return render(request, "transactions.html", context)
