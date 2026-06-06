"""
Alpaca Markets API client.

Wraps the alpaca-py SDK for trading and market data operations, plus provides
raw HTTP access to the activities endpoint (dividends, deposits) which is not
yet exposed in alpaca-py.
"""

from datetime import date, datetime, timezone as dt_timezone
from typing import Any, Dict, List, Optional

import requests
from alpaca.data.enums import DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import QueryOrderStatus
from alpaca.trading.requests import GetOrdersRequest

from stonks_overwatch.config.alpaca import AlpacaConfig
from stonks_overwatch.constants import BrokerName
from stonks_overwatch.services.brokers.alpaca.client.constants import (
    ALPACA_BASE_URL,
    ALPACA_PAPER_BASE_URL,
    ActivityType,
)
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.core.singleton import singleton


class AlpacaOfflineModeError(Exception):
    """Raised when an API call is attempted in offline/demo mode."""

    def __init__(self, message: str):
        """
        Initialize the error.

        Args:
            message: Error message
        """
        super().__init__(message)


@singleton
class AlpacaClient:
    """
    Singleton client for Alpaca Markets API.

    Wraps both TradingClient and StockHistoricalDataClient from alpaca-py,
    using the same API key pair from app.alpaca.markets for both.
    Activities (dividends, deposits) are fetched via raw HTTP.
    """

    logger = StonksLogger.get_logger("stonks_overwatch.alpaca_client", "[ALPACA|CLIENT]")
    _trading_client: Optional[TradingClient] = None
    _data_client: Optional[StockHistoricalDataClient] = None

    def __init__(self, config: Optional[AlpacaConfig] = None):
        """
        Initialize the Alpaca client.

        Args:
            config: Optional AlpacaConfig instance (resolved from factory if not provided)
        """
        if config is not None:
            self.alpaca_config = config
        else:
            try:
                from stonks_overwatch.config.base_config import resolve_config_from_factory

                self.alpaca_config = resolve_config_from_factory(BrokerName.ALPACA, AlpacaConfig)
            except ImportError as e:
                raise ImportError(f"Failed to import BrokerFactory: {e}") from e

        credentials = self.alpaca_config.get_credentials
        if credentials and credentials.has_minimal_credentials():
            paper = self.alpaca_config.paper_trading
            self._trading_client = TradingClient(
                api_key=credentials.api_key,
                secret_key=credentials.secret_key,
                paper=paper,
            )
            self._data_client = StockHistoricalDataClient(
                api_key=credentials.api_key,
                secret_key=credentials.secret_key,
            )
            mode = "paper" if paper else "live"
            self.logger.info(f"Alpaca client initialized in {mode} trading mode")

    def _check_offline_mode(self) -> None:
        """
        Raise AlpacaOfflineModeError if in offline/demo mode.

        Raises:
            AlpacaOfflineModeError: If offline mode is active
        """
        if self.alpaca_config.offline_mode:
            raise AlpacaOfflineModeError("Alpaca working in offline mode. No connection is allowed")

    def _get_trading_client(self) -> TradingClient:
        """
        Return the TradingClient, checking offline mode first.

        Returns:
            TradingClient instance

        Raises:
            AlpacaOfflineModeError: If in offline mode
            RuntimeError: If client is not initialized (no credentials)
        """
        self._check_offline_mode()
        if self._trading_client is None:
            raise RuntimeError("Alpaca TradingClient is not initialized. Check your credentials.")
        return self._trading_client

    def _get_data_client(self) -> StockHistoricalDataClient:
        """
        Return the StockHistoricalDataClient, checking offline mode first.

        Returns:
            StockHistoricalDataClient instance

        Raises:
            AlpacaOfflineModeError: If in offline mode
            RuntimeError: If client is not initialized (no credentials)
        """
        self._check_offline_mode()
        if self._data_client is None:
            raise RuntimeError("Alpaca StockHistoricalDataClient is not initialized. Check your credentials.")
        return self._data_client

    def get_account(self) -> Any:
        """
        Retrieve account information (equity, cash, buying power).

        Returns:
            Alpaca Account object

        Raises:
            AlpacaOfflineModeError: If in offline mode
        """
        self.logger.debug("Retrieving account information")
        return self._get_trading_client().get_account()

    def get_positions(self) -> List[Any]:
        """
        Retrieve all open positions.

        Returns:
            List of Alpaca Position objects

        Raises:
            AlpacaOfflineModeError: If in offline mode
        """
        self.logger.debug("Retrieving open positions")
        return self._get_trading_client().get_all_positions()

    def get_orders(self, after: Optional[date] = None, until: Optional[date] = None) -> List[Any]:
        """
        Retrieve all closed (filled) orders using forward pagination.

        The alpaca-py SDK caps each response at 500 orders.  This method
        pages forward by advancing the ``after`` cursor to the ``submitted_at``
        timestamp of the last order in each batch, accumulating results until
        a page with fewer than 500 items is returned.

        Args:
            after: Only return orders submitted after this date
            until: Only return orders submitted before this date

        Returns:
            List of all matching Alpaca Order objects, oldest first

        Raises:
            AlpacaOfflineModeError: If in offline mode
        """
        page_size = 500
        self.logger.debug(f"Retrieving orders from {after} to {until}")

        # Use an explicit datetime cursor so we can advance it per page.
        # The alpaca-py SDK accepts ISO-8601 strings for the after/until fields.
        current_after: Optional[str] = after.isoformat() if after else None

        all_orders: List[Any] = []
        client = self._get_trading_client()

        while True:
            request_params: Dict[str, Any] = {
                "status": QueryOrderStatus.CLOSED,
                "limit": page_size,
                "direction": "asc",
            }
            if current_after:
                request_params["after"] = current_after
            if until:
                request_params["until"] = until.isoformat()

            page = client.get_orders(filter=GetOrdersRequest(**request_params))
            if not page:
                break

            all_orders.extend(page)
            self.logger.debug(f"Fetched {len(page)} orders (total so far: {len(all_orders)})")

            if len(page) < page_size:
                break

            # Advance cursor to just after the last order's submitted_at so the
            # next page starts from the correct position without duplicates.
            last_submitted = page[-1].submitted_at
            if last_submitted is None:
                break
            if isinstance(last_submitted, datetime):
                current_after = last_submitted.astimezone(dt_timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                current_after = str(last_submitted)

        self.logger.debug(f"Retrieved {len(all_orders)} orders in total")
        return all_orders

    def get_activities(
        self,
        activity_types: Optional[List[ActivityType]] = None,
        after: Optional[date] = None,
        page_size: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve account activities (dividends, deposits, withdrawals) via raw HTTP.

        The alpaca-py SDK does not yet expose get_account_activities(), so this
        method calls the REST endpoint directly.

        Args:
            activity_types: List of activity types to filter by (e.g. [ActivityType.DIV, ActivityType.CSD])
            after: Only return activities after this date
            page_size: Number of results per page

        Returns:
            List of activity dictionaries

        Raises:
            AlpacaOfflineModeError: If in offline mode
            requests.HTTPError: If the API request fails
        """
        self._check_offline_mode()

        credentials = self.alpaca_config.get_credentials
        if not credentials or not credentials.has_minimal_credentials():
            raise RuntimeError("Alpaca credentials are not configured.")

        paper = self.alpaca_config.paper_trading
        base_url = ALPACA_PAPER_BASE_URL if paper else ALPACA_BASE_URL
        url = f"{base_url}/v2/account/activities"

        headers = {
            "APCA-API-KEY-ID": credentials.api_key,
            "APCA-API-SECRET-KEY": credentials.secret_key,
        }

        params: Dict[str, Any] = {
            "direction": "desc",
            "page_size": page_size,
        }
        if activity_types:
            params["activity_types"] = ",".join(at.value for at in activity_types)
        if after:
            params["after"] = after.isoformat()

        all_results: List[Dict[str, Any]] = []
        page_token: Optional[str] = None

        while True:
            if page_token:
                params["page_token"] = page_token

            self.logger.debug(f"Fetching activities: {params}")
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            if not data:
                break

            all_results.extend(data)

            # Alpaca paginates via a page_token in the last item's id
            if len(data) < page_size:
                break
            page_token = data[-1].get("id")
            if not page_token:
                break

        self.logger.debug(f"Retrieved {len(all_results)} activities")
        return all_results

    def get_latest_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Retrieve the latest prices for a list of stock symbols.

        Uses the IEX feed explicitly to avoid errors on free-tier accounts.
        Paid accounts (Algo Trader Plus) automatically get SIP data.

        Args:
            symbols: List of ticker symbols (e.g. ["AAPL", "TSLA"])

        Returns:
            Dictionary mapping symbol to latest ask price

        Raises:
            AlpacaOfflineModeError: If in offline mode
        """
        if not symbols:
            return {}

        self.logger.debug(f"Retrieving latest prices for {symbols}")
        request = StockLatestQuoteRequest(
            symbol_or_symbols=symbols,
            feed=DataFeed.IEX,
        )
        quotes = self._get_data_client().get_stock_latest_quote(request)

        prices: Dict[str, float] = {}
        for symbol, quote in quotes.items():
            ask_price = getattr(quote, "ask_price", None)
            bid_price = getattr(quote, "bid_price", None)
            # Prefer ask_price; fall back to bid_price only when ask is absent.
            # Use explicit None checks so a valid $0.00 ask is not skipped.
            price = ask_price if ask_price is not None else bid_price
            if price is not None:
                prices[symbol] = float(price)

        return prices
