import os
from typing import Optional

from django.core.cache import cache

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.core.interfaces.base_service import DependencyInjectionMixin
from stonks_overwatch.core.interfaces.update_service import AbstractUpdateService
from stonks_overwatch.services.brokers.ibkr.client.ibkr_service import IbkrService
from stonks_overwatch.services.brokers.ibkr.repositories.models import IBKRPosition, IBKRTransactions
from stonks_overwatch.services.brokers.ibkr.repositories.positions_repository import PositionsRepository
from stonks_overwatch.utils.core.debug import save_to_json

CACHE_KEY_UPDATE_PORTFOLIO = "portfolio_data_update_from_ibkr"
# Cache the result for 1 hour (3600 seconds)
CACHE_TIMEOUT = 3600


class UpdateService(DependencyInjectionMixin, AbstractUpdateService):
    def __init__(self, import_folder: str = None, debug_mode: bool = True, config: Optional[BaseConfig] = None):
        """
        Initialize the UpdateService.
        :param import_folder:
            Folder to store the JSON files for debugging purposes.
        :param debug_mode:
            If True, the service will store the JSON files for debugging purposes.
        :param config:
            Optional configuration for dependency injection.
        """
        super().__init__(config)
        AbstractUpdateService.__init__(self, "IBKR", import_folder, debug_mode)

        self.ibkr_service = IbkrService()
        # Use base_currency property from DependencyInjectionMixin which handles dependency injection
        # self.currency = self.base_currency

    def update_all(self):
        if not self.ibkr_service.get_client():
            self.logger.warning("Skipping update since cannot connect to IBKR")
            return

        if self.debug_mode:
            self.logger.warning("Storing JSON files at %s", self.import_folder)

        try:
            self.update_portfolio()
            self.update_transactions()
        except Exception as error:
            self.logger.error("Cannot Update Portfolio!")
            self.logger.error("Exception: %s", str(error))

    def update_portfolio(self):
        """Updating the Portfolio is an expensive and time-consuming task.
        This method caches the result for a period of time.
        """
        self._log_message("Updating Portfolio Data....")

        cached_data = cache.get(CACHE_KEY_UPDATE_PORTFOLIO)

        # If a result is already cached, return it
        if cached_data is None:
            self._log_message("Portfolio data not found in cache. Calling IBKR")
            # Otherwise, call the expensive method
            result = self.__update_portfolio()

            cache.set(CACHE_KEY_UPDATE_PORTFOLIO, result, timeout=CACHE_TIMEOUT)

            return result

        return cached_data

    def update_transactions(self):
        """Update the Account DB data. Only does it if the data is older than today."""
        self._log_message("Updating Transactions Data....")

        transactions = {}
        for position in PositionsRepository.get_all_positions():
            self._log_message(f"Updating transactions for '{position['contractDesc']}' position '{position['conid']}'")
            history = self.ibkr_service.transaction_history(position["conid"], self.base_currency)

            transactions[position["conid"]] = history.get("transactions", {})
            for transaction in history.get("transactions", {}):
                try:
                    transaction_date = self.ibkr_service.convert_date(transaction["date"])
                    self._retry_database_operation(
                        IBKRTransactions.objects.update_or_create,
                        id=f"{transaction['conid']}_{int(transaction_date.timestamp())}",
                        defaults={
                            "acct_id": transaction["acctid"],
                            "conid": transaction["conid"],
                            "date": transaction_date,
                            "cur": transaction["cur"],
                            "fx_rate": transaction["fxRate"],
                            "pr": transaction.get("pr", None),
                            "qty": transaction.get("qty", None),
                            "amt": transaction["amt"],
                            "type": transaction["type"],
                            "desc": transaction["desc"],
                        },
                    )
                except Exception as error:
                    self.logger.error(f"Cannot import transaction: {transaction}")
                    self.logger.error(error, exc_info=True)

        if self.debug_mode:
            transactions_file = os.path.join(self.import_folder, "transactions.json")
            save_to_json(transactions, transactions_file)

    def __update_portfolio(self):
        """Update the Portfolio DB data."""
        open_positions = self.ibkr_service.get_open_positions()

        if self.debug_mode:
            open_positions_file = os.path.join(self.import_folder, "open_positions.json")
            save_to_json(open_positions, open_positions_file)

        self.__import_open_positions(open_positions)

    def __import_open_positions(self, open_positions: list[dict]) -> None:
        """Store the open positions into the DB."""
        for row in open_positions:
            try:
                self._retry_database_operation(
                    IBKRPosition.objects.update_or_create,
                    conid=int(row["conid"]),
                    defaults={
                        "acct_id": row["acctId"],
                        "contract_desc": row["contractDesc"],
                        "position": row["position"],
                        "mkt_price": row.get("mktPrice", None),
                        "mkt_value": row.get("mktValue", None),
                        "currency": row["currency"],
                        "avg_cost": row.get("avgCost", None),
                        "avg_price": row.get("avgPrice", None),
                        "realized_pnl": row.get("realizedPnl", None),
                        "unrealized_pnl": row.get("unrealizedPnl", None),
                        "base_avg_cost": row.get("baseAvgCost", None),
                        "base_avg_price": row.get("baseAvgPrice", None),
                        "base_realized_pnl": row.get("baseRealizedPnl", None),
                        "base_unrealized_pnl": row.get("baseUnrealizedPnl", None),
                        "asset_class": row["assetClass"],
                        "type": row["type"],
                        "listing_exchange": row["listingExchange"],
                        "country_code": row["countryCode"],
                        "name": row["name"],
                        "group": row["group"],
                        "sector": row["sector"],
                        "sector_group": row["sectorGroup"],
                        "ticker": row["ticker"],
                        "full_name": row["fullName"],
                        "is_us": row["isUS"],
                    },
                )
            except Exception as error:
                self.logger.error(f"Cannot import position: {row}")
                self.logger.error("Exception: %s", str(error), exc_info=True)
