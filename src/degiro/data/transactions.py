from datetime import date

from degiro_connector.trading.models.transaction import HistoryRequest

from degiro.config.degiro_config import DegiroConfig
from degiro.models import Transactions
from degiro.repositories.product_info_repository import ProductInfoRepository
from degiro.repositories.transactions_repository import TransactionsRepository
from degiro.utils.debug import save_to_json
from degiro.utils.degiro import DeGiro
from degiro.utils.localization import LocalizationUtility


class TransactionsData:
    def __init__(self):
        self.transactions_repository = TransactionsRepository()
        self.product_info_repository = ProductInfoRepository()

    def get_transactions(self) -> dict:
        self.update_transactions()
        return self.__get_transactions()

    def update_transactions(self, debug_json_files: dict = None):
        """Update the Account DB data. Only does it if the data is older than today."""
        today = date.today()
        last_movement = self.transactions_repository.get_last_movement()
        if last_movement is None:
            last_movement = DegiroConfig.default().start_date

        if last_movement < today:
            transactions_history = self.__get_transaction_history(last_movement)
            if debug_json_files and "transactions.json" in debug_json_files:
                save_to_json(transactions_history, debug_json_files["transactions.json"])

            self.__import_transactions(transactions_history)

    def __get_transactions(self) -> dict:
        # FETCH TRANSACTIONS DATA
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

        # DISPLAY PRODUCTS_INFO
        my_transactions = []
        for transaction in transactions_history:
            info = products_info[transaction["productId"]]

            fees = transaction["totalPlusFeeInBaseCurrency"] - transaction["totalInBaseCurrency"]

            my_transactions.append(
                {
                    "name": info["name"],
                    "symbol": info["symbol"],
                    "date": transaction["date"].strftime(LocalizationUtility.DATE_FORMAT),
                    "time": transaction["date"].strftime(LocalizationUtility.TIME_FORMAT),
                    "buysell": self.__convert_buy_sell(transaction["buysell"]),
                    "transactionType": self.__convert_transaction_type_id(transaction["transactionTypeId"]),
                    "price": LocalizationUtility.format_money_value(transaction["price"], currency=info["currency"]),
                    "quantity": transaction["quantity"],
                    "total": LocalizationUtility.format_money_value(
                        value=transaction["total"], currency=info["currency"]
                    ),
                    "totalInBaseCurrency": LocalizationUtility.format_money_value(
                        value=transaction["totalInBaseCurrency"],
                        currency_symbol=base_currency_symbol,
                    ),
                    "fees": LocalizationUtility.format_money_value(value=fees, currency_symbol=base_currency_symbol),
                }
            )

        return sorted(my_transactions, key=lambda k: k["date"], reverse=True)

    def __convert_buy_sell(self, buysell: str) -> str:
        if buysell == "B":
            return "Buy"
        elif buysell == "S":
            return "Sell"

        return "Unknown"

    def __convert_transaction_type_id(self, transaction_type_id: int) -> str:
        return {
            0: "",
            101: "Stock Split",
        }.get(transaction_type_id, "Unkown Transaction")

    def __get_transaction_history(self, from_date: date) -> date:
        """Import Transactions data from DeGiro. Uses the `get_transactions_history` method."""
        trading_api = DeGiro.get_client()

        # FETCH DATA
        return trading_api.get_transactions_history(
            transaction_request=HistoryRequest(from_date=from_date, to_date=date.today()),
            raw=True,
        )


    def __import_transactions(self, transactions_history: dict) -> None:
        """Store the Transactions into the DB."""

        for row in transactions_history["data"]:
            try:
                Transactions.objects.update_or_create(
                    id=row["id"],
                    defaults={
                        "product_id": row["productId"],
                        "date": LocalizationUtility.convert_string_to_datetime(row["date"]),
                        "buysell": row["buysell"],
                        "price": row["price"],
                        "quantity": row["quantity"],
                        "total": row["total"],
                        "order_type_id": row.get("orderTypeId", None),
                        "counter_party": row.get("counterParty", None),
                        "transfered": row["transfered"],
                        "fx_rate": row["fxRate"],
                        "nett_fx_rate": row["nettFxRate"],
                        "gross_fx_rate": row["grossFxRate"],
                        "auto_fx_fee_in_base_currency": row["autoFxFeeInBaseCurrency"],
                        "total_in_base_currency": row["totalInBaseCurrency"],
                        "fee_in_base_currency": row.get("feeInBaseCurrency", None),
                        "total_fees_in_base_currency": row["totalFeesInBaseCurrency"],
                        "total_plus_fee_in_base_currency": row["totalPlusFeeInBaseCurrency"],
                        "total_plus_all_fees_in_base_currency": row["totalPlusAllFeesInBaseCurrency"],
                        "transaction_type_id": row["transactionTypeId"],
                        "trading_venue": row.get("tradingVenue", None),
                        "executing_entity_id": row.get("executingEntityId", None),
                    },
                )
            except Exception as error:
                print(f"Cannot import row: {row}")
                print("Exception: ", error)
