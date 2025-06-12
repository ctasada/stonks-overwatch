from stonks_overwatch.config.config import Config
from stonks_overwatch.utils.localization import LocalizationUtility

from .currency_service import CurrencyConverterService
from ..client.degiro_client import DeGiroService
from ..repositories.cash_movements_repository import CashMovementsRepository
from ..repositories.product_info_repository import ProductInfoRepository
from ..repositories.transactions_repository import TransactionsRepository

class FeesService:

    def __init__(
            self,
            degiro_service: DeGiroService,
    ):
        self.currency_service = CurrencyConverterService()
        self.degiro_service = degiro_service
        self.base_currency = Config.default().base_currency

    def get_fees(self) -> list[dict]:
        transaction_fees = self.get_transaction_fees()
        account_fees = self.get_account_fees()

        total_fees = account_fees + transaction_fees

        return sorted(total_fees, key=lambda k: (k["date"], k["time"]), reverse=True)

    def get_account_fees(self) -> list[dict]:
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
                {
                    "date": cash_movement["date"].strftime(LocalizationUtility.DATE_FORMAT),
                    "time": cash_movement["date"].strftime(LocalizationUtility.TIME_FORMAT),
                    "type": fee_type,
                    "description": cash_movement["description"],
                    "fee_value": fee_value,
                    "fees": LocalizationUtility.format_money_value(value=fee_value, currency=currency_value),
                }
            )

        return my_fees

    def __get_fee_type(self, description: str) -> str | None:
        # description = "Spanish Transaction Tax" -> FTT (Finance Transaction Tax)
        # description = "ADR/GDR Externe Kosten" -> ADR/GDR
        # description = "DEGIRO Aansluitingskosten" -> Connection
        if "Transaction Tax" in description:
            return "Finance Transaction Tax"
        elif "DEGIRO Aansluitingskosten" in description:
            return "Connection"
        elif "ADR/GDR Externe Kosten" in description:
            return "ADR/GDR"
        else:
            return None

    def get_transaction_fees(self) -> list[dict]:
        transactions_history = TransactionsRepository.get_transactions_raw()

        products_ids = []

        # ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
        for transaction in transactions_history:
            products_ids.append(int(transaction["productId"]))

        # Remove duplicates from list
        products_ids = list(set(products_ids))
        products_info = ProductInfoRepository.get_products_info_raw(products_ids)

        # Get user's base currency
        base_currency_symbol = LocalizationUtility.get_currency_symbol(self.base_currency)

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
                {
                    "date": transaction["date"].strftime(LocalizationUtility.DATE_FORMAT),
                    "time": transaction["date"].strftime(LocalizationUtility.TIME_FORMAT),
                    "type": "Transaction",
                    "description": description,
                    "fee_value": fees,
                    "fees": LocalizationUtility.format_money_value(value=fees, currency_symbol=base_currency_symbol),
                }
            )

        return my_fees

    def __convert_buy_sell(self, buysell: str) -> str:
        if buysell == "B":
            return "Bought"
        elif buysell == "S":
            return "Sold"

        return "Unknown"
