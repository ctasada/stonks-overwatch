"""Alpaca update service implementation."""

from typing import Any, Dict, List, Optional

from django.db import transaction

from stonks_overwatch.config.alpaca import AlpacaConfig
from stonks_overwatch.constants import BrokerName
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.core.interfaces.update_service import AbstractUpdateService
from stonks_overwatch.services.brokers.alpaca.client.alpaca_client import AlpacaClient
from stonks_overwatch.services.brokers.alpaca.client.constants import (
    DEPOSIT_ACTIVITY_TYPES,
    DIVIDEND_ACTIVITY_TYPES,
)
from stonks_overwatch.services.brokers.alpaca.repositories.models import AlpacaActivity, AlpacaOrder, AlpacaPosition
from stonks_overwatch.utils.core.logger import StonksLogger


class UpdateService(BaseService, AbstractUpdateService):
    """
    Update service for Alpaca Markets.

    Syncs positions, orders, and activities (dividends, deposits) from the
    Alpaca API into the local database for use by the read services.
    """

    logger = StonksLogger.get_logger("stonks_overwatch.alpaca.update_service", "[ALPACA|UPDATE]")

    def __init__(
        self,
        import_folder: Optional[str] = None,
        debug_mode: Optional[bool] = None,
        config: Optional[AlpacaConfig] = None,
    ):
        """
        Initialize the UpdateService.

        Args:
            import_folder: Folder to store JSON files for debugging
            debug_mode: If True, stores raw JSON responses for debugging
            config: Optional configuration instance for dependency injection
        """
        AbstractUpdateService.__init__(self, BrokerName.ALPACA, import_folder, debug_mode, config)
        self._injected_config = config
        self._global_config = None
        self.alpaca_client = AlpacaClient()

    def update_all(self) -> None:
        """
        Sync all Alpaca data: positions, orders, and activities.

        Skips if the client is in offline mode or credentials are not configured.
        """
        if self.alpaca_client.alpaca_config.offline_mode:
            self.logger.warning("Skipping update since Alpaca is in offline mode")
            return

        if (
            not self.alpaca_client.alpaca_config.get_credentials
            or not self.alpaca_client.alpaca_config.get_credentials.has_minimal_credentials()
        ):
            self.logger.warning("Skipping Alpaca update: no credentials configured")
            return

        try:
            self.update_positions()
            self.update_orders()
            self.update_activities()
            self._record_sync(success=True)
        except Exception as error:
            self.logger.error("Cannot update Alpaca data!")
            self.logger.error("Exception: %s", str(error), exc_info=True)
            self._record_sync(success=False)

    def update_positions(self) -> None:
        """Fetch open positions from Alpaca and upsert them into the DB."""
        self._log_message("Updating Alpaca positions...")
        try:
            positions = self.alpaca_client.get_positions()
            self._import_positions(positions)
        except Exception as error:
            self.logger.error("Failed to update Alpaca positions: %s", str(error), exc_info=True)
            raise

    def update_orders(self) -> None:
        """Fetch all closed orders from Alpaca and upsert them into the DB."""
        self._log_message("Updating Alpaca orders...")
        try:
            config = self.alpaca_client.alpaca_config
            after = config.start_date if config else None
            orders = self.alpaca_client.get_orders(after=after)
            self._import_orders(orders)
        except Exception as error:
            self.logger.error("Failed to update Alpaca orders: %s", str(error), exc_info=True)
            raise

    def update_activities(self) -> None:
        """Fetch dividend and deposit activities from Alpaca and upsert them into the DB."""
        self._log_message("Updating Alpaca activities...")
        try:
            all_types = DIVIDEND_ACTIVITY_TYPES + DEPOSIT_ACTIVITY_TYPES
            config = self.alpaca_client.alpaca_config
            after = config.start_date if config else None
            activities = self.alpaca_client.get_activities(activity_types=all_types, after=after)
            self._import_activities(activities)
        except Exception as error:
            self.logger.error("Failed to update Alpaca activities: %s", str(error), exc_info=True)
            raise

    def _import_positions(self, positions: List[Any]) -> None:
        """Clear and repopulate the positions table from live API data.

        The delete and all subsequent writes are wrapped in a single atomic
        transaction so that concurrent reads via ``get_portfolio`` never observe
        a partially-cleared table.
        """
        with transaction.atomic():
            AlpacaPosition.objects.all().delete()
            for position in positions:
                try:
                    self._retry_database_operation(
                        AlpacaPosition.objects.update_or_create,
                        symbol=str(position.symbol),
                        defaults={
                            "qty": str(position.qty),
                            "avg_entry_price": str(position.avg_entry_price) if position.avg_entry_price else None,
                            "market_value": str(position.market_value) if position.market_value else None,
                            "current_price": str(position.current_price) if position.current_price else None,
                            "unrealized_pl": str(position.unrealized_pl) if position.unrealized_pl else None,
                            "cost_basis": str(position.cost_basis) if position.cost_basis else None,
                            "side": str(position.side.value) if hasattr(position.side, "value") else str(position.side),
                            "currency": str(position.currency) if hasattr(position, "currency") else "USD",
                        },
                    )
                except Exception as error:
                    self.logger.error(f"Cannot import position {getattr(position, 'symbol', '?')}: {error}")

    def _import_orders(self, orders: List[Any]) -> None:
        """Upsert orders into the DB, keyed by order_id."""
        for order in orders:
            try:
                self._retry_database_operation(
                    AlpacaOrder.objects.update_or_create,
                    order_id=str(order.id),
                    defaults={
                        "symbol": str(order.symbol),
                        "qty": str(order.qty) if order.qty else None,
                        "filled_qty": str(order.filled_qty) if order.filled_qty else None,
                        "filled_avg_price": str(order.filled_avg_price) if order.filled_avg_price else None,
                        "side": str(order.side.value) if hasattr(order.side, "value") else str(order.side),
                        "order_type": str(order.order_type.value)
                        if hasattr(order.order_type, "value")
                        else str(order.order_type),
                        "status": str(order.status.value) if hasattr(order.status, "value") else str(order.status),
                        "submitted_at": order.submitted_at,
                        "filled_at": order.filled_at,
                    },
                )
            except Exception as error:
                self.logger.error(f"Cannot import order {getattr(order, 'id', '?')}: {error}")

    def _import_activities(self, activities: List[Dict[str, Any]]) -> None:
        """Upsert activities into the DB, keyed by activity id."""
        for activity in activities:
            try:
                activity_id = activity.get("id", "")
                if not activity_id:
                    self.logger.warning(f"Activity missing ID, skipping: {activity}")
                    continue

                activity_date_raw = activity.get("date") or activity.get("transaction_time")
                if activity_date_raw and "T" in str(activity_date_raw):
                    activity_date_raw = str(activity_date_raw).split("T")[0]

                self._retry_database_operation(
                    AlpacaActivity.objects.update_or_create,
                    activity_id=str(activity_id),
                    defaults={
                        "activity_type": activity.get("activity_type", ""),
                        "symbol": activity.get("symbol"),
                        "qty": activity.get("qty"),
                        "price": activity.get("price"),
                        "net_amount": activity.get("net_amount"),
                        "per_share_amount": activity.get("per_share_amount"),
                        "activity_date": activity_date_raw,
                        "description": activity.get("description"),
                    },
                )
            except Exception as error:
                self.logger.error(f"Cannot import activity {activity.get('id', '?')}: {error}")
