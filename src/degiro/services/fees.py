from currency_converter import CurrencyConverter

from degiro.repositories.cash_movements_repository import CashMovementsRepository
from degiro.repositories.product_info_repository import ProductInfoRepository
from degiro.repositories.transactions_repository import TransactionsRepository
from degiro.utils.localization import LocalizationUtility


class FeesService:
    currency_converter = CurrencyConverter(fallback_on_missing_rate=True, fallback_on_wrong_date=True)

    def __init__(self):
        self.cash_movements_repository = CashMovementsRepository()
        self.product_info_repository = ProductInfoRepository()
        self.transactions_repository = TransactionsRepository()

    def get_fees(self) -> dict:
        transaction_fees = self.get_transaction_fees()
        account_fees = self.get_account_fees()

        total_fees = account_fees + transaction_fees

        return sorted(total_fees, key=lambda k: k["date"], reverse=True)

    def get_account_fees(self) -> dict:
        cash_movements = self.cash_movements_repository.get_cash_movements_raw()
        base_currency = LocalizationUtility.get_base_currency()

        my_fees = []
        for cash_movement in cash_movements:
            fee_type = self.__get_fee_type(cash_movement["description"])
            if fee_type is None:
                continue

            fee_value = cash_movement["change"]
            currency_value = cash_movement["currency"]
            if currency_value != base_currency:
                fx_date = cash_movement["date"].date()
                fee_value = self.currency_converter.convert(fee_value, currency_value, base_currency, fx_date)
                currency_value = base_currency

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

    def __get_fee_type(self, description: str) -> str:
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

    def get_transaction_fees(self) -> dict:
        transactions_history = self.transactions_repository.get_transactions_raw()

        products_ids = []

        # ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
        for transaction in transactions_history:
            products_ids.append(int(transaction["productId"]))

        # Remove duplicates from list
        products_ids = list(set(products_ids))
        products_info = self.product_info_repository.get_products_info_raw(products_ids)

        # Get user's base currency
        base_currency_symbol = LocalizationUtility.get_base_currency_symbol()

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
