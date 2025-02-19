import dataclasses

from django.shortcuts import render
from django.views import View

from stonks_overwatch.services.session_manager import SessionManager
from stonks_overwatch.services.transactions_aggregator import TransactionsAggregatorService


class Transactions(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transactions = TransactionsAggregatorService()

    def get(self, request):
        selected_portfolio = SessionManager.get_selected_portfolio(request)
        transactions = self.transactions.get_transactions(selected_portfolio)

        context = {
            "transactions": [dataclasses.asdict(transaction) for transaction in transactions],
        }

        return render(request, "transactions.html", context)
