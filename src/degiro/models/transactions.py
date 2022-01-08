from degiro.utils.degiro import DeGiro
from degiro.utils.localization import LocalizationUtility

from degiro_connector.trading.models.trading_pb2 import TransactionsHistory
from datetime import date
import json

class TransactionsModel:
    def __init__(self):
        self.deGiro = DeGiro()

    def get_transactions(self):
        # SETUP REQUEST
        today = date.today()
        from_date = TransactionsHistory.Request.Date(
            year=2020,
            month=1,
            day=1,
        )
        to_date = TransactionsHistory.Request.Date(
            year=today.year,
            month=today.month,
            day=today.day,
        )
        request = TransactionsHistory.Request(
            from_date=from_date,
            to_date=to_date,
        )

        # FETCH TRANSACTIONS DATA
        transactions_history = DeGiro.get_client().get_transactions_history(
            request=request,
            raw=False,
        )

        products_ids = []

        # ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
        for transaction in transactions_history.values:
            products_ids.append(int(transaction['productId']))

        products_info = DeGiro.get_products_info(products_ids)

        # Get user's base currency
        baseCurrencySymbol = LocalizationUtility.get_base_currency_symbol()

        # DISPLAY PRODUCTS_INFO
        myTransactions = []
        for transaction in transactions_history.values:
            info = products_info[str(int(transaction['productId']))]

            fees = transaction['totalPlusFeeInBaseCurrency'] - transaction['totalInBaseCurrency']

            myTransactions.append(
                dict(
                    name=info['name'],
                    symbol = info['symbol'],
                    date = LocalizationUtility.format_date_time(transaction['date']),
                    buysell = self.convertBuySell(transaction['buysell']),
                    transactionType = self.convertTransactionTypeId(transaction['transactionTypeId']),
                    price = transaction['price'],
                    quantity = transaction['quantity'],
                    total = LocalizationUtility.format_money_value(value = transaction['total'], currency = info['currency']),
                    totalInBaseCurrency = LocalizationUtility.format_money_value(value = transaction['totalInBaseCurrency'], currencySymbol = baseCurrencySymbol),
                    fees = LocalizationUtility.format_money_value(value = fees, currencySymbol = baseCurrencySymbol)
                )
            )

        return sorted(myTransactions, key=lambda k: k['date'])

    def convertBuySell(self, buysell: str):
        if (buysell == "B"):
            return "Buy"
        elif (buysell == "S"):
            return "Sell"
        
        return "Unknown"

    def convertTransactionTypeId(self, transactionTypeId: int):
        return {
            0: "",
            101: "Stock Split",
        }.get(transactionTypeId, "Unkown Transaction")