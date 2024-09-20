from django.shortcuts import render
from django.views import View

from degiro.repositories.product_info_repository import ProductInfoRepository
from degiro.repositories.transactions_repository import TransactionsRepository
from degiro.services.transactions import TransactionsService


class Transactions(View):
    def __init__(self):
        self.product_info_repository = ProductInfoRepository()
        self.transactions_repository = TransactionsRepository()

        self.transactions = TransactionsService(
            product_info_repository=self.product_info_repository,
            transactions_repository=self.transactions_repository,
        )

    def get(self, request):
        transactions = self.transactions.get_transactions()

        context = {
            "transactions": transactions,
        }

        return render(request, "transactions.html", context)
