from django.http import HttpResponse
from django.http import JsonResponse
from django.views import View
from django.shortcuts import render

from degiro.models.transactions import TransactionsModel

import json

class Transactions(View):
    def __init__(self):
        self.transactions = TransactionsModel()

    def get(self, request):
        transactions = self.transactions.get_transactions()

        # print (json.dumps(transactions, indent=2))

        context = {
            "transactions": transactions,
        }

        return render(request, 'transactions.html', context)
