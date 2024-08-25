from degiro.repositories.cash_movements_repository import CashMovementsRepository
from degiro.repositories.product_info_repository import ProductInfoRepository
from degiro.repositories.transactions_repository import TransactionsRepository
from degiro.utils.localization import LocalizationUtility
from currency_converter import CurrencyConverter


class FeesData:
    currencyConverter = CurrencyConverter(
        fallback_on_missing_rate=True, fallback_on_wrong_date=True
    )

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
        baseCurrency = LocalizationUtility.get_base_currency()

        myFees = []
        for cash_movement in cash_movements:
            feeType = self.__get_fee_type(cash_movement["description"])
            if feeType is None:
                continue

            fee_value = cash_movement["change"]
            currency_value = cash_movement["currency"]
            if currency_value != baseCurrency:
                fx_date = cash_movement["date"].date()
                fee_value = self.currencyConverter.convert(fee_value, currency_value, baseCurrency, fx_date)
                currency_value = baseCurrency

            myFees.append(
                dict(
                    date=cash_movement["date"].strftime(LocalizationUtility.DATE_FORMAT),
                    time=cash_movement["date"].strftime(LocalizationUtility.TIME_FORMAT),
                    type=feeType,
                    description=cash_movement["description"],
                    fee_value=fee_value,
                    fees=LocalizationUtility.format_money_value(value=fee_value, currency=currency_value),
                )
            )

        return myFees

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
        baseCurrencySymbol = LocalizationUtility.get_base_currency_symbol()

        myFees = []
        for transaction in transactions_history:
            info = products_info[transaction["productId"]]
            # FIXME: # feeInBaseCurrency vs totalFeesInBaseCurrency
            fees = transaction["totalFeesInBaseCurrency"]

            if fees is None or fees == 0:
                continue

            buySell = self.__convertBuySell(transaction["buysell"])
            stockName = info["name"]
            stockPrice = LocalizationUtility.format_money_value(value=transaction["price"], currency=info["currency"])
            stockQuantity = abs(transaction["quantity"])

            description = f"{buySell} {stockQuantity}x {stockName} @ {stockPrice}"

            myFees.append(
                dict(
                    date=transaction["date"].strftime(LocalizationUtility.DATE_FORMAT),
                    time=transaction["date"].strftime(LocalizationUtility.TIME_FORMAT),
                    type="Transaction",
                    description=description,
                    fee_value=fees,
                    fees=LocalizationUtility.format_money_value(
                        value=fees, currencySymbol=baseCurrencySymbol
                    ),
                )
            )

        return myFees

    def __convertBuySell(self, buysell: str) -> str:
        if buysell == "B":
            return "Bought"
        elif buysell == "S":
            return "Sold"

        return "Unknown"
