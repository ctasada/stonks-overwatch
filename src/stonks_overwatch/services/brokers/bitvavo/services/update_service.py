import os
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from typing import Optional

from degiro_connector.quotecast.models.chart import Interval
from django.utils import timezone

from stonks_overwatch.config.bitvavo import BitvavoConfig
from stonks_overwatch.constants import BrokerName
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.core.interfaces.update_service import AbstractUpdateService
from stonks_overwatch.services.brokers.bitvavo.client.bitvavo_client import BitvavoService
from stonks_overwatch.services.brokers.bitvavo.repositories.models import (
    BitvavoAssets,
    BitvavoBalance,
    BitvavoProductQuotation,
    BitvavoTransactions,
)
from stonks_overwatch.services.brokers.bitvavo.services.portfolio_service import PortfolioService
from stonks_overwatch.utils.core.datetime import DateTimeUtility
from stonks_overwatch.utils.core.debug import save_to_json
from stonks_overwatch.utils.core.localization import LocalizationUtility
from stonks_overwatch.utils.core.logger import StonksLogger


class UpdateService(BaseService, AbstractUpdateService):
    logger = StonksLogger.get_logger("stonks_overwatch.bitvavo.update_service", "[BITVAVO|UPDATE]")

    def __init__(self, import_folder: str = None, debug_mode: bool = None, config: Optional[BitvavoConfig] = None):
        """
        Initialize the UpdateService.
        :param import_folder:
            Folder to store the JSON files for debugging purposes.
        :param debug_mode:
            If True, the service will store the JSON files for debugging purposes.
        :param config:
            Optional configuration instance for dependency injection.
        """
        # Initialize AbstractUpdateService first (has no super() calls to interfere)
        AbstractUpdateService.__init__(self, BrokerName.BITVAVO, import_folder, debug_mode, config)
        # Then manually set BaseService attributes without calling its __init__
        self._injected_config = config
        self._global_config = None

        self.bitvavo_service = BitvavoService()
        self.portfolio_data = PortfolioService()
        # Use base_currency property from BaseService which handles dependency injection
        self.currency = self.base_currency

    def update_all(self):
        if not self.bitvavo_service.get_client():
            self.logger.warning("Skipping update since cannot connect to BITVAVO")
            return

        if self.debug_mode:
            self.logger.info("Storing JSON files at %s", self.import_folder)

        try:
            self.update_transactions()
            self.update_portfolio()
            self.update_assets()
            self._record_sync(success=True)
        except Exception as error:
            self.logger.error("Cannot Update Portfolio!")
            self.logger.error("Exception: %s", str(error), exc_info=True)
            self._record_sync(success=False)

    def update_portfolio(self):
        self._log_message("Updating Portfolio Data....")

        """Update the Portfolio DB data."""
        balance = self.bitvavo_service.balance()
        staking_balance = self.bitvavo_service.staking_balance()

        if self.debug_mode:
            balance_file = os.path.join(self.import_folder, "balance.json")
            save_to_json(balance, balance_file)
            staking_balance_file = os.path.join(self.import_folder, "staking_balance.json")
            save_to_json(staking_balance, staking_balance_file)

        self.__import_balance(balance + staking_balance)
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
        self.__deduplicate_transactions()

    def __import_quotation(self) -> None:  # noqa: C901
        product_growth = self.portfolio_data.calculate_product_growth()

        delete_keys = []
        today = LocalizationUtility.format_date_from_date(timezone.now().date())

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

        start_date = LocalizationUtility.ensure_aware(
            LocalizationUtility.convert_string_to_datetime(product_history_dates[0])
        )
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
        # Clear existing balances to avoid stale data
        BitvavoBalance.objects.all().delete()
        for row in balance:
            try:
                self._retry_database_operation(
                    BitvavoBalance.objects.update_or_create,
                    symbol=row["symbol"],
                    defaults={
                        # balance() returns {"available": ...}; staking_balance() returns {"amount": ...}.
                        # If the same symbol appears in both lists the staking entry wins (it comes second),
                        # storing only the staked amount. This is intentional: the raw balance is used only
                        # as an upper-bound sanity check in BalanceRepository._merge_with_raw_balance.
                        "available": row.get("available", row.get("amount")),
                    },
                )
            except Exception as error:
                self.logger.error(f"Cannot import position: {row}")
                self.logger.error("Exception: %s", str(error), exc_info=True)

    # Matches DecimalField(decimal_places=10) precision used in BitvavoTransactions.
    _DECIMAL_QUANTIZE = Decimal("0.0000000001")

    @staticmethod
    def __to_decimal(value: str | float | None) -> Decimal | None:
        if value is None:
            return None
        try:
            return Decimal(str(value)).quantize(UpdateService._DECIMAL_QUANTIZE)
        except InvalidOperation:
            return None

    def __import_transactions(self, transactions: list[dict]) -> None:
        # Sort the transactions by executedAt to ensure they are processed in the correct order
        transactions.sort(key=lambda item: item["executedAt"])
        for row in transactions:
            try:
                # Bitvavo API bug: the same trade can appear on multiple pages with a different transactionId.
                # Skip if a content-identical record already exists under a different ID.
                # __deduplicate_transactions is the authoritative cleanup; this check avoids inserting in the
                # first place when precision allows a reliable match.
                duplicate_exists = (
                    BitvavoTransactions.objects.filter(
                        executed_at=row["executedAt"],
                        type=row["type"],
                        sent_currency=row.get("sentCurrency"),
                        sent_amount=self.__to_decimal(row.get("sentAmount")),
                        received_currency=row.get("receivedCurrency"),
                        received_amount=self.__to_decimal(row.get("receivedAmount")),
                    )
                    .exclude(transaction_id=row["transactionId"])
                    .exists()
                )
                if duplicate_exists:
                    self.logger.debug(
                        f"Skipping duplicate transaction {row['transactionId']} (same content, different ID)"
                    )
                    continue

                self._retry_database_operation(
                    BitvavoTransactions.objects.update_or_create,
                    transaction_id=row["transactionId"],
                    defaults={
                        "executed_at": row["executedAt"],
                        "type": row["type"],
                        "price_currency": row.get("priceCurrency", None),
                        "price_amount": row.get("priceAmount", None),
                        "sent_currency": row.get("sentCurrency", None),
                        "sent_amount": row.get("sentAmount", None),
                        "received_currency": row.get("receivedCurrency", None),
                        "received_amount": row.get("receivedAmount", None),
                        "fees_currency": row.get("feesCurrency", None),
                        "fees_amount": row.get("feesAmount", None),
                        "address": row.get("address", None),
                    },
                )
            except Exception as error:
                self.logger.error(f"Cannot import position: {row}")
                self.logger.error("Exception: %s", str(error), exc_info=True)

    def __deduplicate_transactions(self) -> None:
        """Remove transactions that are content-identical but have different transactionIds (Bitvavo API bug)."""
        seen: set[tuple] = set()
        to_delete: list[int] = []

        for txn in BitvavoTransactions.objects.order_by("executed_at", "id").only(
            "id", "executed_at", "type", "sent_currency", "sent_amount", "received_currency", "received_amount"
        ):
            fingerprint = (
                txn.executed_at,
                txn.type,
                txn.sent_currency,
                txn.sent_amount,
                txn.received_currency,
                txn.received_amount,
            )
            if fingerprint in seen:
                to_delete.append(txn.id)
            else:
                seen.add(fingerprint)

        if to_delete:
            count, _ = BitvavoTransactions.objects.filter(id__in=to_delete).delete()
            self.logger.info(f"Removed {count} duplicate transaction(s)")

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
