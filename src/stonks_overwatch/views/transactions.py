import dataclasses

from django.shortcuts import render
from django.views import View

from stonks_overwatch.services.transactions_aggregator import TransactionsAggregatorService


class Transactions(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transactions = TransactionsAggregatorService()

    def get(self, request):
        transactions = self.transactions.get_transactions()

        context = {
            "transactions": [dataclasses.asdict(transaction) for transaction in transactions],
        }

        return render(request, "transactions.html", context)
