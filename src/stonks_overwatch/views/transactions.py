from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from stonks_overwatch.core.service_types import ServiceType
from stonks_overwatch.services.aggregators.transactions_aggregator import TransactionsAggregatorService
from stonks_overwatch.services.models import dataclass_to_dict
from stonks_overwatch.services.utilities.session_manager import SessionManager
from stonks_overwatch.views.mixins import CapabilityRequiredMixin


class Transactions(CapabilityRequiredMixin, View):
    required_capability = ServiceType.TRANSACTION

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transactions = TransactionsAggregatorService()

    def get(self, request):
        selected_portfolio = SessionManager.get_selected_portfolio(request)
        transactions = self.transactions.get_transactions(selected_portfolio)
        transactions_data = [dataclass_to_dict(transaction) for transaction in transactions]

        if request.headers.get("Accept") == "application/json":
            return JsonResponse({"transactions": transactions_data}, safe=False)
        else:
            context = {"transactions": transactions_data}
            return render(request, "transactions.html", context)
