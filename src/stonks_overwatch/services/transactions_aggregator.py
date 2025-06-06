from typing import List

from stonks_overwatch.config.config import Config
from stonks_overwatch.services.bitvavo.transactions import TransactionsService as BitvavoTransactionsService
from stonks_overwatch.services.degiro.degiro_service import DeGiroService
from stonks_overwatch.services.degiro.transactions import TransactionsService as DeGiroTransactionsService
from stonks_overwatch.services.models import PortfolioId, Transaction

class TransactionsAggregatorService:

    def __init__(self):
        self.degiro_service = DeGiroService()
        self.degiro_transactions = DeGiroTransactionsService(
            degiro_service=self.degiro_service,
        )
        self.bitvavo_transactions = BitvavoTransactionsService()

    def get_transactions(self, selected_portfolio: PortfolioId) -> List[Transaction]:
        transactions = []
        if Config.default().is_degiro_enabled(selected_portfolio):
            transactions += self.degiro_transactions.get_transactions()

        if Config.default().is_bitvavo_enabled(selected_portfolio):
            transactions += self.bitvavo_transactions.get_transactions()

        return sorted(transactions, key=lambda k: (k.date, k.time, 1 if k.buy_sell == "S" else 0), reverse=True)
