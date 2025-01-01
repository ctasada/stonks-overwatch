from stonks_overwatch.config import Config
from stonks_overwatch.repositories.degiro.product_info_repository import ProductInfoRepository
from stonks_overwatch.repositories.degiro.transactions_repository import TransactionsRepository
from stonks_overwatch.services.degiro.degiro_service import DeGiroService
from stonks_overwatch.utils.constants import TransactionType
from stonks_overwatch.utils.localization import LocalizationUtility


class TransactionsService:
    def __init__(
            self,
            degiro_service: DeGiroService,
    ):
        self.degiro_service = degiro_service
        self.base_currency = Config.default().base_currency

    def get_transactions(self) -> list[dict]:
        # FETCH TRANSACTIONS DATA
        transactions_history = TransactionsRepository.get_transactions_raw()

        products_ids = []

        # ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
        for transaction in transactions_history:
            products_ids.append(int(transaction["productId"]))

        # Remove duplicates from list
        products_ids = list(set(products_ids))
        products_info = ProductInfoRepository.get_products_info_raw(products_ids)

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
                    "transactionType": TransactionType.from_int(transaction["transactionTypeId"]).to_string(),
                    "price": LocalizationUtility.format_money_value(transaction["price"], currency=info["currency"]),
                    "quantity": transaction["quantity"],
                    "total": LocalizationUtility.format_money_value(
                        value=transaction["total"], currency=info["currency"]
                    ),
                    "totalInBaseCurrency": LocalizationUtility.format_money_value(
                        value=transaction["totalInBaseCurrency"],
                        currency=self.base_currency,
                    ),
                    "fees": LocalizationUtility.format_money_value(value=fees, currency=self.base_currency),
                }
            )

        return sorted(my_transactions, key=lambda k: (k["date"], k["time"]), reverse=True)

    def __convert_buy_sell(self, buy_sell: str) -> str:
        if buy_sell == "B":
            return "Buy"
        elif buy_sell == "S":
            return "Sell"

        return "Unknown"

