from datetime import datetime, timezone as dt_timezone
from typing import Any, Optional

from python_bitvavo_api.bitvavo import Bitvavo, createPostfix

from stonks_overwatch.config.bitvavo import BitvavoConfig
from stonks_overwatch.constants import BrokerName
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.core.singleton import singleton


class BitvavoOfflineModeError(Exception):
    """Exception raised for data validation errors."""

    def __init__(self, message):
        """
        Initializes the exception with a message and a structure of error details.

        Args:
            message (str): The error message.
        """
        super().__init__(message)


@singleton
class BitvavoService:
    START_TIMESTAMP = 0

    logger = StonksLogger.get_logger("stonks_overwatch.bitvavo_service", "[BITVAVO|CLIENT]")
    _client: Bitvavo = None
    force: bool = False

    def __init__(
        self,
        debugging: bool = False,
        force: bool = False,
        config: Optional[BitvavoConfig] = None,
    ):
        self.force = force

        # Use dependency injection if config is provided, otherwise fallback to global config
        if config is not None:
            self.bitvavo_config = config
        else:
            # Get Bitvavo configuration using unified BrokerFactory
            try:
                from stonks_overwatch.config.base_config import resolve_config_from_factory

                # Get and resolve Bitvavo configuration
                self.bitvavo_config = resolve_config_from_factory(BrokerName.BITVAVO, BitvavoConfig)
            except ImportError as e:
                raise ImportError(f"Failed to import BrokerFactory: {e}") from e

        bitvavo_credentials = self.bitvavo_config.get_credentials

        if bitvavo_credentials and bitvavo_credentials.apikey and bitvavo_credentials.apisecret:
            self._client = Bitvavo(
                {
                    "APIKEY": bitvavo_credentials.apikey,
                    "APISECRET": bitvavo_credentials.apisecret,
                    "debugging": debugging,
                }
            )

    def get_client(self) -> Bitvavo:
        if not self.force and self.bitvavo_config.offline_mode:
            raise BitvavoOfflineModeError("Bitvavo working in offline mode. No connection is allowed")

        return self._client

    def get_remaining_limit(self) -> int:
        return self.get_client().getRemainingLimit()

    def account(self) -> Any:
        """Returns the current fees for this account."""
        self.logger.debug("Retrieving account")
        return self.get_client().account()

    def account_history(self) -> Any:
        """Returns the transaction history for this account."""
        self.logger.debug("Retrieving account history")
        options = {"fromDate": self.START_TIMESTAMP}

        all_results = []
        current_page = 1
        while True:
            options["page"] = current_page
            postfix = createPostfix(options)
            response = self.get_client().privateRequest("/account/history", postfix, {}, "GET")

            if not response or "items" not in response:
                break

            all_results.extend(response["items"])

            if "totalPages" in response and current_page < response["totalPages"]:
                current_page += 1
            else:
                break

        return all_results

    def assets(self, symbol: str = None) -> Any:
        """Returns information on the supported assets."""
        self.logger.debug(f"Retrieving assets for symbol {symbol}")
        options = {}
        if symbol:
            options["symbol"] = symbol
        return self.get_client().assets(options)

    def balance(self, symbol: str = None) -> Any:
        """Returns the current balance for this account."""
        self.logger.debug(f"Retrieving balance for symbol {symbol}")
        options = {}
        if symbol:
            options["symbol"] = symbol
        return self.get_client().balance(options)

    def candles(self, market: str, interval: str, start: datetime, end: datetime = None) -> list[dict]:
        """
        Retrieve the Open, High, Low, Close, Volume (OHLCV) data you use to create candlestick charts for market with
        interval time between each candlestick.
        Candlestick data is always returned in chronological data from oldest to newest. Data is returned when trades
        are made in the interval represented by that candlestick. When no trades occur you see a gap in data flow,
        zero trades are represented by zero candlesticks.
        """
        self.logger.debug(f"Retrieving candles for market {market} with interval {interval} from {start} to {end}")
        # FIXME: Return a maximum of limit candlesticks for trades made from start.
        #  If interval is longer we need to split the request in multiple requests.
        response = self.get_client().candles(market, interval, {}, start=start, end=end)
        result = []
        for candle in response:
            result.append(
                {
                    "timestamp": datetime.fromtimestamp(candle[0] / 1000, tz=dt_timezone.utc),
                    "open": candle[1],
                    "high": candle[2],
                    "low": candle[3],
                    "close": candle[4],
                    "volume": candle[5],
                }
            )
        return sorted(result, key=lambda k: k["timestamp"])

    def deposit_history(self) -> Any:
        """Returns the deposit history of the account."""
        self.logger.debug("Retrieving deposit history")
        return self.get_client().depositHistory()

    def ticker_price(self, market: str = None) -> Any:
        """Retrieve the price of the latest trades on Bitvavo for all markets or a single market."""
        self.logger.debug(f"Retrieving ticker price for market {market}")
        options = {}
        if market:
            options["market"] = market
        return self.get_client().tickerPrice(options)

    def withdrawal_history(self) -> Any:
        """Returns the withdrawal history."""
        self.logger.debug("Retrieving withdrawal history")
        return self.get_client().withdrawalHistory()
