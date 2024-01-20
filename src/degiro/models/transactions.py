from degiro.utils.degiro import DeGiro
from degiro.utils.localization import LocalizationUtility

from degiro_connector.trading.models.transaction import HistoryRequest
from datetime import date
import json
import logging

class TransactionsModel:
    def __init__(self):
        self.deGiro = DeGiro()

    def get_transactions(self):
        # SETUP REQUEST
        today = date.today()
        from_date = date(
            year=2020,
            month=1,
            day=1,
        )
        to_date = date(
            year=today.year,
            month=today.month,
            day=today.day,
        )
        logging.basicConfig(level=logging.DEBUG)
        # FETCH TRANSACTIONS DATA
        transactions_history = DeGiro.get_client().get_transactions_history(
            transaction_request=HistoryRequest(
                from_date=from_date,
                to_date=to_date,
            ),
            raw=True,
        )

        products_ids = []

        # ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
        for transaction in transactions_history['data']:
            products_ids.append(int(transaction['productId']))

        products_info = DeGiro.get_products_info(products_ids)

        # Get user's base currency
        baseCurrencySymbol = LocalizationUtility.get_base_currency_symbol()

        # DISPLAY PRODUCTS_INFO
        myTransactions = []
        for transaction in transactions_history['data']:
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

        return sorted(myTransactions, key=lambda k: k['date'], reverse=True)

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