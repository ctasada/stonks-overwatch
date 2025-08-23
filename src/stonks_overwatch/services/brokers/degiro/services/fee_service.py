from typing import Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.core.interfaces.fee_service import FeeServiceInterface
from stonks_overwatch.services.brokers.degiro.client.degiro_client import DeGiroService
from stonks_overwatch.services.brokers.degiro.repositories.cash_movements_repository import CashMovementsRepository
from stonks_overwatch.services.brokers.degiro.repositories.product_info_repository import ProductInfoRepository
from stonks_overwatch.services.brokers.degiro.repositories.transactions_repository import TransactionsRepository
from stonks_overwatch.services.brokers.degiro.services.currency_service import CurrencyConverterService
from stonks_overwatch.services.models import Fee, FeeType
from stonks_overwatch.utils.core.localization import LocalizationUtility


class FeesService(FeeServiceInterface, BaseService):
    def __init__(
        self,
        degiro_service: Optional[DeGiroService] = None,
        config: Optional[BaseConfig] = None,
    ):
        super().__init__(config)
        self.currency_service = CurrencyConverterService()
        self.degiro_service = degiro_service or DeGiroService()

    # Note: base_currency property is inherited from BaseService and handles
    # dependency injection automatically

    def get_fees(self) -> list[Fee]:
        transaction_fees = self.get_transaction_fees()
        account_fees = self.get_account_fees()

        total_fees = account_fees + transaction_fees

        return sorted(total_fees, key=lambda k: (k.date, k.time), reverse=True)

    def get_account_fees(self) -> list[Fee]:
        cash_movements = CashMovementsRepository.get_cash_movements_raw()

        my_fees = []
        for cash_movement in cash_movements:
            fee_type = self.__get_fee_type(cash_movement["description"])
            if fee_type is None:
                continue

            fee_value = cash_movement["change"]
            currency_value = cash_movement["currency"]
            if currency_value != self.base_currency:
                fx_date = cash_movement["date"].date()
                fee_value = self.currency_service.convert(fee_value, currency_value, self.base_currency, fx_date)
                currency_value = self.base_currency

            my_fees.append(
                Fee(
                    date=cash_movement["date"].strftime(LocalizationUtility.DATE_FORMAT),
                    time=cash_movement["date"].strftime(LocalizationUtility.TIME_FORMAT),
                    type=fee_type,
                    description=cash_movement["description"],
                    fee_value=fee_value,
                    currency=currency_value,
                )
            )

        return my_fees

    def __get_fee_type(self, description: str) -> FeeType | None:
        # description = "Spanish Transaction Tax" -> FTT (Finance Transaction Tax)
        # description = "ADR/GDR Externe Kosten" -> ADR/GDR
        # description = "DEGIRO Aansluitingskosten" -> Connection
        if "Transaction Tax" in description:
            return FeeType.FINANCE_TRANSACTION_TAX
        elif "DEGIRO Aansluitingskosten" in description:
            return FeeType.CONNECTION
        elif "ADR/GDR Externe Kosten" in description:
            return FeeType.ADR_GDR
        else:
            return None

    def get_transaction_fees(self) -> list[Fee]:
        transactions_history = TransactionsRepository.get_transactions_raw()

        products_ids = []

        # ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
        for transaction in transactions_history:
            products_ids.append(int(transaction["productId"]))

        # Remove duplicates from list
        products_ids = list(set(products_ids))
        products_info = ProductInfoRepository.get_products_info_raw(products_ids)

        my_fees = []
        for transaction in transactions_history:
            info = products_info[transaction["productId"]]
            # FIXME: # feeInBaseCurrency vs totalFeesInBaseCurrency
            fees = transaction["totalFeesInBaseCurrency"]

            if fees is None or fees == 0:
                continue

            buy_sell = self.__convert_buy_sell(transaction["buysell"])
            stock_name = info["name"]
            stock_price = LocalizationUtility.format_money_value(value=transaction["price"], currency=info["currency"])
            stock_quantity = abs(transaction["quantity"])

            description = f"{buy_sell} {stock_quantity}x {stock_name} @ {stock_price}"

            my_fees.append(
                Fee(
                    date=transaction["date"].strftime(LocalizationUtility.DATE_FORMAT),
                    time=transaction["date"].strftime(LocalizationUtility.TIME_FORMAT),
                    type=FeeType.TRANSACTION,
                    description=description,
                    fee_value=fees,
                    currency=self.base_currency,
                )
            )

        return my_fees

    def __convert_buy_sell(self, buysell: str) -> str:
        if buysell == "B":
            return "Bought"
        elif buysell == "S":
            return "Sold"

        return "Unknown"
