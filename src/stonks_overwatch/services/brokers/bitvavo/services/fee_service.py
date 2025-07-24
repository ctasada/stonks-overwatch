from stonks_overwatch.config.config import Config
from stonks_overwatch.services.brokers.bitvavo.client.bitvavo_client import BitvavoService
from stonks_overwatch.services.brokers.bitvavo.services.transaction_service import TransactionsService
from stonks_overwatch.services.models import Fee, FeeType


class FeesService:
    def __init__(self):
        self.bitvavo_service = BitvavoService()
        self.base_currency = Config.get_global().base_currency

    def get_fees(self) -> list[dict]:
        transactions_history = self.bitvavo_service.account_history()
        total_fees = []
        for transaction in transactions_history:
            if transaction["type"] == "deposit":
                continue

            if "feesAmount" not in transaction:
                continue

            fee_value = float(transaction["feesAmount"])
            transaction_type = self.__convert_buy_sell(transaction["type"])
            description = f"{transaction_type} {transaction['receivedCurrency']} Transaction Fee"

            total_fees.append(
                Fee(
                    date=TransactionsService.format_date(transaction["executedAt"]),
                    time=TransactionsService.format_time(transaction["executedAt"]),
                    type=FeeType.TRANSACTION,
                    description=description,
                    fee_value=fee_value,
                    currency=transaction["feesCurrency"],
                )
            )

        return sorted(total_fees, key=lambda k: k.datetime, reverse=True)

    def __convert_buy_sell(self, buy_sell: str) -> str:
        if buy_sell in ["buy", "staking"]:
            return "Bought"
        elif buy_sell == "sell":
            return "Sold"

        return "Unknown"
