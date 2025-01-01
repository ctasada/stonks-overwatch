from stonks_overwatch.config import Config
from stonks_overwatch.services.degiro.degiro_service import DeGiroService
from stonks_overwatch.services.degiro.transactions import TransactionsService as DeGiroTransactionsService


class TransactionsAggregatorService:

    def __init__(self):
        self.degiro_service = DeGiroService()
        self.degiro_transactions = DeGiroTransactionsService(
            degiro_service=self.degiro_service,
        )

    def get_transactions(self) -> list[dict]:
        transactions = []
        if Config.default().is_degiro_enabled():
            transactions += self.degiro_transactions.get_transactions()

        return sorted(transactions, key=lambda k: (k["date"], k["time"]), reverse=True)
