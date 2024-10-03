from enum import Enum

from degiro.repositories.product_info_repository import ProductInfoRepository
from degiro.repositories.transactions_repository import TransactionsRepository
from degiro.utils.localization import LocalizationUtility


class TransactionsService:

    def get_transactions(self) -> dict:
        # FETCH TRANSACTIONS DATA
        transactions_history = TransactionsRepository.get_transactions_raw()

        products_ids = []

        # ITERATION OVER THE TRANSACTIONS TO OBTAIN THE PRODUCTS
        for transaction in transactions_history:
            products_ids.append(int(transaction["productId"]))

        # Remove duplicates from list
        products_ids = list(set(products_ids))
        products_info = ProductInfoRepository.get_products_info_raw(products_ids)

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
                    "transactionType": TransactionType.from_int(transaction["transactionTypeId"]).to_string(),
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


class TransactionType(Enum):
    """
    Enum representing various transaction types in DeGiro's API.

    - 0: Stock buy/sell
    - 101: Stock Split
    - 102: Dividend payment
    - 106: Corporate actions (e.g., stock splits, stock dividends)
    """

    BUY_SELL = 0
    """Represents the buying or selling of a Stock."""

    STOCK_SPLIT = 101
    """Represents a Stock Split."""

    DIVIDEND = 102
    """Represents a Dividend payment."""

    CORPORATE_ACTION = 106  # Relates with Stock Dividends
    """Represents a Corporate action, such as stock splits, corporation rename or stock dividends."""

    # INTEREST = 108 # Could be reverse split, but also stock dividends or interests
    # """Represents Interest payments, e.g., for margin or balances (transactionTypeId 108)."""
    #
    # WITHDRAWAL = 110 # Seems also related with stock dividends
    # """Represents Withdrawals from funds (transactionTypeId 110)."""
    #
    # FEES = 112 # Seems also related with stock dividends
    # """Represents Fees, such as transaction or management fees (transactionTypeId 112)."""
    #
    # DEPOSIT = 114 # Seems also related with stock dividends
    # """Represents Deposits into the trading account (transactionTypeId 114)."""

    UNKNOWN = -1
    """Represents an unknown transaction type."""

    @staticmethod
    def from_int(value: int):
        try:
            return TransactionType(value)
        except ValueError:
            return TransactionType.UNKNOWN

    def to_string(self):
        readable_strings = {
            TransactionType.BUY_SELL: "",
            TransactionType.STOCK_SPLIT: "Stock Split",
            TransactionType.DIVIDEND: "Dividend Payment",
            TransactionType.CORPORATE_ACTION: "Corporate Action",
        }
        return readable_strings.get(self, "Unknown Transaction Type")


class ProductType(Enum):
    STOCK = 1
    """Represents a Stock product."""

    BONDS = 2
    FUTURES = 7
    OPTIONS = 8
    FUNDS = 13
    LEVERAGE_PRODUCTS = 14

    ETF = 131
    """Represents an ETF product."""

    INDEX = 180

    CASH = 311
    """Represents a Cash product."""

    CFDS = 535
    WARRANTS = 536

    UNKNOWN = -1
    """Represents an unknown product type."""

    @staticmethod
    def from_int(value: int):
        try:
            return ProductType(value)
        except ValueError:
            return ProductType.UNKNOWN

    def to_string(self):
        readable_strings = {
            ProductType.STOCK: "Stock",
            ProductType.ETF: "ETF",
            ProductType.CASH: "Cash",
        }
        return readable_strings.get(self, "Unknown Product Type")
