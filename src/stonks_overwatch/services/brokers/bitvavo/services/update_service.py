import os
from datetime import date, datetime, timedelta, timezone

from degiro_connector.quotecast.models.chart import Interval

from stonks_overwatch.config.config import Config
from stonks_overwatch.core.interfaces.update_service import AbstractUpdateService
from stonks_overwatch.services.brokers.bitvavo.client.bitvavo_client import BitvavoService
from stonks_overwatch.services.brokers.bitvavo.repositories.models import (
    BitvavoAssets,
    BitvavoBalance,
    BitvavoDepositHistory,
    BitvavoProductQuotation,
    BitvavoTransactions,
)
from stonks_overwatch.services.brokers.bitvavo.services.portfolio_service import PortfolioService
from stonks_overwatch.utils.core.datetime import DateTimeUtility
from stonks_overwatch.utils.core.debug import save_to_json
from stonks_overwatch.utils.core.localization import LocalizationUtility
from stonks_overwatch.utils.core.logger import StonksLogger


class UpdateService(AbstractUpdateService):
    logger = StonksLogger.get_logger("stonks_overwatch.bitvavo.update_service", "[BITVAVO|UPDATE]")

    def __init__(self, import_folder: str = None, debug_mode: bool = True):
        """
        Initialize the UpdateService.
        :param import_folder:
            Folder to store the JSON files for debugging purposes.
        :param debug_mode:
            If True, the service will store the JSON files for debugging purposes.
        """
        super().__init__("Bitvavo", import_folder, debug_mode)

        self.bitvavo_service = BitvavoService()
        self.portfolio_data = PortfolioService()
        self.currency = Config.get_global().base_currency

    def update_all(self):
        if not self.bitvavo_service.get_client():
            self.logger.warning("Skipping update since cannot connect to BITVAVO")
            return

        if self.debug_mode:
            self.logger.warning("Storing JSON files at %s", self.import_folder)

        try:
            self.update_transactions()
            self.update_deposits()
            self.update_portfolio()
            self.update_assets()
        except Exception as error:
            self.logger.error("Cannot Update Portfolio!")
            self.logger.error("Exception: %s", str(error), exc_info=True)

    def update_portfolio(self):
        self._log_message("Updating Portfolio Data....")

        """Update the Portfolio DB data."""
        balance = self.bitvavo_service.balance()

        if self.debug_mode:
            balance_file = os.path.join(self.import_folder, "balance.json")
            save_to_json(balance, balance_file)

        self.__import_balance(balance)
        self.__import_quotation()

    def update_assets(self):
        """Update the Account DB data. Only does it if the data is older than today."""
        self._log_message("Updating Assets Data....")

        assets = self.bitvavo_service.assets()

        if self.debug_mode:
            assets_file = os.path.join(self.import_folder, "assets.json")
            save_to_json(assets, assets_file)

        self.__import_assets(assets)

    def update_transactions(self):
        """Update the Account DB data. Only does it if the data is older than today."""
        self._log_message("Updating Transactions Data....")

        transactions = self.bitvavo_service.account_history()

        if self.debug_mode:
            transactions_file = os.path.join(self.import_folder, "transactions.json")
            save_to_json(transactions, transactions_file)

        self.__import_transactions(transactions)

    def update_deposits(self):
        """Update the Account DB data. Only does it if the data is older than today."""
        self._log_message("Updating Deposits Data....")

        # Bitvavo does not have a separate deposit history endpoint, so we use the account history
        deposits = self.bitvavo_service.deposit_history()

        if self.debug_mode:
            deposits_file = os.path.join(self.import_folder, "deposits.json")
            save_to_json(deposits, deposits_file)

        self.__import_deposits(deposits)

    def __import_quotation(self) -> None:  # noqa: C901
        product_growth = self.portfolio_data.calculate_product_growth()

        delete_keys = []
        today = LocalizationUtility.format_date_from_date(date.today())

        for key in product_growth.keys():
            # Calculate Quotation Range
            product_growth[key]["quotation"] = {}
            product_history_dates = list(product_growth[key]["history"].keys())
            start_date = product_history_dates[0]
            final_date = today
            tmp_last = product_history_dates[-1]
            if product_growth[key]["history"][tmp_last] == 0:
                final_date = tmp_last

            product_growth[key]["quotation"]["from_date"] = start_date
            product_growth[key]["quotation"]["to_date"] = final_date
            # Interval should be from start_date, since the QuoteCast query doesn't support more granularity
            product_growth[key]["quotation"]["interval"] = DateTimeUtility.calculate_interval(start_date)

        # Delete the non-tradable products
        for key in delete_keys:
            del product_growth[key]

        # We need to use the productIds to get the daily quote for each product
        for key in product_growth.keys():
            interval = product_growth[key]["quotation"]["interval"]
            quotes_dict = self._create_products_quotation(key, product_growth[key])

            if not quotes_dict:
                self.logger.info(f"Quotation not found for '{key}' / {interval}")
                continue

            # Update the data ONLY if we get something back from DeGiro
            if quotes_dict:
                self._retry_database_operation(
                    BitvavoProductQuotation.objects.update_or_create,
                    symbol=key,
                    defaults={
                        "interval": Interval.P1D,
                        "last_import": LocalizationUtility.now(),
                        "quotations": quotes_dict,
                    },
                )

    def _create_products_quotation(self, symbol: str, data: dict) -> dict:
        product_history_dates = list(data["history"].keys())

        start_date = LocalizationUtility.convert_string_to_datetime(product_history_dates[0])
        candles = self.bitvavo_service.candles(f"{symbol}-{self.currency}", "1d", start_date)
        # Creates the dictionary with the date as key and the value as the close price
        date_to_value = {
            start_date + timedelta(days=i): candle["close"]
            for i, candle in enumerate(candles)
            if candle["timestamp"] >= start_date
        }
        quotes = {
            LocalizationUtility.format_date_from_date(date): float(value) for date, value in date_to_value.items()
        }

        return quotes

    def __import_balance(self, balance: list[dict]) -> None:
        for row in balance:
            try:
                self._retry_database_operation(
                    BitvavoBalance.objects.update_or_create,
                    symbol=row["symbol"],
                    available=row["available"],
                )
            except Exception as error:
                self.logger.error(f"Cannot import position: {row}")
                self.logger.error("Exception: %s", str(error), exc_info=True)

    def __import_transactions(self, balance: list[dict]) -> None:
        # Sort the transactions by executedAt to ensure they are processed in the correct order
        balance.sort(key=lambda item: item["executedAt"])
        for row in balance:
            try:
                self._retry_database_operation(
                    BitvavoTransactions.objects.update_or_create,
                    transaction_id=row["transactionId"],
                    executed_at=row["executedAt"],
                    type=row["type"],
                    price_currency=row.get("priceCurrency", None),
                    price_amount=row.get("priceAmount", None),
                    sent_currency=row.get("sentCurrency", None),
                    sent_amount=row.get("sentAmount", None),
                    received_currency=row.get("receivedCurrency", None),
                    received_amount=row.get("receivedAmount", None),
                    fees_currency=row.get("feesCurrency", None),
                    fees_amount=row.get("feesAmount", None),
                    address=row.get("address", None),
                )
            except Exception as error:
                self.logger.error(f"Cannot import position: {row}")
                self.logger.error("Exception: %s", str(error), exc_info=True)

    def __import_deposits(self, deposits: list[dict]) -> None:
        for row in deposits:
            try:
                self._retry_database_operation(
                    BitvavoDepositHistory.objects.update_or_create,
                    timestamp=datetime.fromtimestamp(row["timestamp"] / 1000.0, tz=timezone.utc),
                    symbol=row["symbol"],
                    amount=row["amount"],
                    address=row.get("address", None),
                    payment_id=row.get("paymentId", None),
                    tx_id=row.get("txId", None),
                    fee=row.get("fee", None),
                    status=row["status"],
                )
            except Exception as error:
                self.logger.error(f"Cannot import deposit: {row}")
                self.logger.error("Exception: %s", str(error), exc_info=True)

    def __import_assets(self, assets: list[dict]) -> None:
        for row in assets:
            try:
                self._retry_database_operation(
                    BitvavoAssets.objects.update_or_create,
                    symbol=row["symbol"],
                    defaults={
                        "name": row.get("name", None),
                        "decimals": row.get("decimals", 0),
                        "deposit_fee": row.get("depositFee", None),
                        "deposit_confirmations": row.get("depositConfirmations", 0),
                        "deposit_status": row.get("depositStatus", ""),
                        "withdrawal_fee": row.get("withdrawalFee", None),
                        "withdrawal_min_amount": row.get("withdrawalMinAmount", None),
                        "withdrawal_status": row.get("withdrawalStatus", ""),
                        "networks": row.get("networks", []),
                        "message": row.get("message", None),
                    },
                )
            except Exception as error:
                self.logger.error(f"Cannot import asset: {row}")
                self.logger.error("Exception: %s", str(error), exc_info=True)
