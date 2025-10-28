from typing import List, Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.core.interfaces.fee_service import FeeServiceInterface
from stonks_overwatch.services.brokers.bitvavo.client.bitvavo_client import BitvavoService
from stonks_overwatch.services.brokers.bitvavo.services.trade_service import TradesService
from stonks_overwatch.services.models import Fee, FeeType


class FeeService(FeeServiceInterface, BaseService):
    def __init__(self, config: Optional[BaseConfig] = None):
        super().__init__(config)
        self.bitvavo_service = BitvavoService()

    # Note: base_currency property is inherited from BaseService and handles
    # dependency injection automatically

    def get_fees(self) -> List[Fee]:
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
                    date=TradesService.format_date(transaction["executedAt"]),
                    time=TradesService.format_time(transaction["executedAt"]),
                    type=FeeType.TRANSACTION,
                    description=description,
                    fee_value=fee_value,
                    currency=transaction["feesCurrency"],
                )
            )

        return sorted(total_fees, key=lambda k: (k.date, k.time), reverse=True)

    def __convert_buy_sell(self, buy_sell: str) -> str:
        if buy_sell in ["buy", "staking"]:
            return "Bought"
        elif buy_sell == "sell":
            return "Sold"

        return "Unknown"
