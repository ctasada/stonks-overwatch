from degiro.utils.degiro import DeGiro
import datetime
from trading.api import API as TradingAPI
from trading.pb.trading_pb2 import (
    Credentials,
    ProductsInfo,
    TransactionsHistory,
)
import quotecast.helpers.pb_handler as pb_handler
import json

class TransactionsModel:
    def __init__(self):
        self.deGiro = DeGiro()

    def get_transactions(self):
        # SETUP REQUEST
        today = datetime.date.today()
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
        transactions_history = self.deGiro.getClient().get_transactions_history(
            request=request,
            raw=False,
        )

        products_ids = []

        # ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
        for transaction in transactions_history.values:
            products_ids.append(int(transaction['productId']))

        products_ids = list(set(products_ids))

        # SETUP REQUEST
        request = ProductsInfo.Request()
        request.products.extend(products_ids)

        # FETCH DATA
        products_info = self.deGiro.getClient().get_products_info(
            request=request,
            raw=True,
        )
        print (json.dumps(products_info, indent=2))

        # DISPLAY PRODUCTS_INFO
        myTransactions = []
        for transaction in transactions_history.values:
            info = products_info['data'][str(int(transaction['productId']))]
            myTransactions.append(
                dict(
                    name=info['name'],
                    symbol = info['symbol'],
                    date = transaction['date'],
                    buysell = transaction['buysell'],
                    price = transaction['price'],
                    quantity = transaction['quantity'],
                )
            )

        return sorted(myTransactions, key=lambda k: k['date'])
