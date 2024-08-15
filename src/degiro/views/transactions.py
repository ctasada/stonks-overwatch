from django.views import View
from django.shortcuts import render

from degiro.integration.transactions import TransactionsData


class Transactions(View):
    def __init__(self):
        self.transactions = TransactionsData()

    def get(self, request):
        transactions = self.transactions.get_transactions()

        # print (json.dumps(transactions, indent=2))

        context = {
            "transactions": transactions,
        }

        return render(request, 'transactions.html', context)
