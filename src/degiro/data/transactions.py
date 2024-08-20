from django.db import connection
from degiro.utils.db_utils import dictfetchall
from degiro.utils.localization import LocalizationUtility


# FIXME: If data cannot be found in the DB, the code should get it from DeGiro, updating the DB
class TransactionsData:

    def get_transactions(self):
        # FETCH TRANSACTIONS DATA
        transactions_history = self.__getTransactions()

        products_ids = []

        # ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
        for transaction in transactions_history:
            products_ids.append(int(transaction["productId"]))

        products_info = self.__getProductsInfo(products_ids)

        # Get user's base currency
        baseCurrencySymbol = LocalizationUtility.get_base_currency_symbol()

        # DISPLAY PRODUCTS_INFO
        myTransactions = []
        for transaction in transactions_history:
            info = products_info[transaction["productId"]]

            fees = (
                transaction["totalPlusFeeInBaseCurrency"]
                - transaction["totalInBaseCurrency"]
            )

            myTransactions.append(
                dict(
                    name=info["name"],
                    symbol=info["symbol"],
                    date=transaction["date"],
                    buysell=self.__convertBuySell(transaction["buysell"]),
                    transactionType=self.__convertTransactionTypeId(
                        transaction["transactionTypeId"]
                    ),
                    price=transaction["price"],
                    quantity=transaction["quantity"],
                    total=LocalizationUtility.format_money_value(
                        value=transaction["total"], currency=info["currency"]
                    ),
                    totalInBaseCurrency=LocalizationUtility.format_money_value(
                        value=transaction["totalInBaseCurrency"],
                        currencySymbol=baseCurrencySymbol,
                    ),
                    fees=LocalizationUtility.format_money_value(
                        value=fees, currencySymbol=baseCurrencySymbol
                    ),
                )
            )

        return sorted(myTransactions, key=lambda k: k["date"], reverse=True)

    def __convertBuySell(self, buysell: str):
        if buysell == "B":
            return "Buy"
        elif buysell == "S":
            return "Sell"

        return "Unknown"

    def __convertTransactionTypeId(self, transactionTypeId: int):
        return {
            0: "",
            101: "Stock Split",
        }.get(transactionTypeId, "Unkown Transaction")

    def __getTransactions(self):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM degiro_transactions
                """
            )
            return dictfetchall(cursor)

    def __getProductsInfo(self, ids):
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT *
                FROM degiro_productinfo
                WHERE id IN ({", ".join(map(str, ids))})
                """
            )
            rows = dictfetchall(cursor)

        # Convert the list of dictionaries into a dictionary indexed by 'productId'
        result_map = {row['id']: row for row in rows}
        return result_map
