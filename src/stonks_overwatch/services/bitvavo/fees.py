from stonks_overwatch.config.config import Config
from stonks_overwatch.services.bitvavo.bitvavo_service import BitvavoService
from stonks_overwatch.services.bitvavo.transactions import TransactionsService
from stonks_overwatch.utils.localization import LocalizationUtility

class FeesService:

    def __init__(self):
        self.bitvavo_service = BitvavoService()
        self.base_currency = Config.default().base_currency

    def get_fees(self) -> list[dict]:
        transactions_history = self.bitvavo_service.account_history()
        total_fees = []
        for transaction in transactions_history["items"]:
            if transaction["type"] == "deposit":
                continue

            if "feesAmount" not in transaction:
                continue

            fee_value = float(transaction["feesAmount"])
            transaction_type = self.__convert_buy_sell(transaction["type"])
            description = f"{transaction_type} {transaction['receivedCurrency']} Transaction Fee"

            total_fees.append(
                {
                    "date": TransactionsService.format_date(transaction["executedAt"]),
                    "time": TransactionsService.format_time(transaction["executedAt"]),
                    "type": "Transaction",
                    "description": description,
                    "fee_value": fee_value,
                    "fees": LocalizationUtility.format_money_value(
                        value=fee_value, currency=transaction["feesCurrency"]
                    ),
                }
            )

        return sorted(total_fees, key=lambda k: (k["date"], k["time"]), reverse=True)

    def __convert_buy_sell(self, buy_sell: str) -> str:
        if buy_sell in ["buy", "staking"]:
            return "Bought"
        elif buy_sell == "sell":
            return "Sold"

        return "Unknown"
