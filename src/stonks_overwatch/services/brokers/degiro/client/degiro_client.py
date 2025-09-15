import os
from datetime import date, datetime, timedelta
from typing import Any, List, Optional

import polars as pl
import requests_cache
from degiro_connector.core.exceptions import DeGiroConnectionError, MaintenanceError
from degiro_connector.quotecast.models.chart import Chart, ChartRequest, Interval
from degiro_connector.quotecast.tools.chart_fetcher import ChartFetcher
from degiro_connector.trading.api import API as TradingApi  # noqa: N811
from degiro_connector.trading.models.agenda import AgendaRequest, CalendarType
from degiro_connector.trading.models.credentials import Credentials

import stonks_overwatch.settings
from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.degiro import DegiroConfig, DegiroCredentials
from stonks_overwatch.settings import TIME_ZONE
from stonks_overwatch.utils.core.localization import LocalizationUtility
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.core.singleton import singleton


class DeGiroOfflineModeError(Exception):
    """Exception raised for data validation errors."""

    def __init__(self, message):
        """
        Initializes the exception with a message and a structure of error details.

        Args:
            message (str): The error message.
        """
        super().__init__(message)


class CredentialsManager:
    """Manages the credentials for the DeGiro API."""

    def __init__(self, credentials: Optional[DegiroCredentials] = None, config: Optional[DegiroConfig] = None):
        # Use dependency injection if config is provided, otherwise fallback to global config
        if config is not None:
            degiro_config = config
        else:
            # Get DeGiro configuration using unified BrokerFactory
            try:
                from stonks_overwatch.config.base_config import resolve_config_from_factory

                # Get and resolve DeGiro configuration
                degiro_config = resolve_config_from_factory("degiro", DegiroConfig)
            except ImportError as e:
                raise ImportError(f"Failed to import BrokerFactory: {e}") from e

        degiro_credentials = degiro_config.credentials

        self.credentials = credentials or Credentials(
            int_account=getattr(credentials, "int_account", None) or getattr(degiro_credentials, "int_account", None),
            username=getattr(credentials, "username", "") or getattr(degiro_credentials, "username", ""),
            password=getattr(credentials, "password", "") or getattr(degiro_credentials, "password", ""),
            totp_secret_key=getattr(credentials, "totp_secret_key", None)
            or getattr(degiro_credentials, "totp_secret_key", None),
            one_time_password=getattr(credentials, "one_time_password", None)
            or getattr(degiro_credentials, "one_time_password", None),
        )

    def are_credentials_valid(self) -> bool:
        """Checks if credentials contains, at least, username and password."""
        if (
            not self.credentials
            or not hasattr(self.credentials, "username")
            or not hasattr(self.credentials, "password")
        ):
            return False
        return bool(self.credentials.username and self.credentials.password)

    def __repr__(self) -> str:
        """
        Return a string representation of the CredentialsManager.
        Sensitive data is masked for security.
        """

        def mask_string(value: str | None, visible_chars: int = 4) -> str:
            if not value:
                return "None"
            if len(value) <= visible_chars:
                return "*" * len(value)
            return f"{value[:visible_chars]}{'*' * (len(value) - visible_chars)}"

        credentials = self.credentials
        return (
            f"CredentialsManager("
            f"username='{mask_string(credentials.username)}', "
            f"password='{mask_string(credentials.password, 0)}', "  # Fully mask password
            f"int_account={credentials.int_account}, "
            f"totp_secret_key='{mask_string(credentials.totp_secret_key, 0)}', "  # Fully mask TOTP
            f"one_time_password={mask_string(str(credentials.one_time_password), 0)}"  # Fully mask OTP
            f")"
        )


@singleton
class DeGiroService:
    """
    Singleton service for DeGiro API operations and data access.

    This class implements a singleton pattern to ensure only one instance exists
    throughout the application lifecycle. It focuses purely on API operations
    such as data retrieval, portfolio operations, and trading functionality.

    Authentication Coordination:
    - Authentication flow is handled by AuthenticationService
    - This service receives credentials and manages the API client
    - No longer responsible for global configuration updates
    - Focused on API operations and data access

    Usage:
        # Set credentials for API operations (typically called by AuthenticationService)
        service = DeGiroService()
        service.set_credentials(credentials_manager)

        # Use for API operations
        client = service.get_client()
        portfolio_data = service.get_portfolio()

        # Check API connection status
        is_connected = service.is_connected()
    """

    logger = StonksLogger.get_logger("stonks_overwatch.degiro_service", "[DEGIRO|CLIENT]")
    api_client: TradingApi = None
    credentials_manager: Optional[CredentialsManager] = None
    degiro_config: Optional[DegiroConfig] = None
    force: bool = False
    is_maintenance_mode: bool = False

    __cache_path = os.path.join(stonks_overwatch.settings.STONKS_OVERWATCH_CACHE_DIR, "http_request.cache")

    def __init__(
        self,
        credentials_manager: Optional[CredentialsManager] = None,
        force: bool = False,
        config: Optional[BaseConfig] = None,
    ):
        # Initialize configuration - this will be provided by AuthenticationService
        self.degiro_config = config
        if self.degiro_config is None:
            # Fallback to BrokerFactory for backward compatibility
            try:
                from stonks_overwatch.config.base_config import resolve_config_from_factory

                # Get and resolve DeGiro configuration
                self.degiro_config = resolve_config_from_factory("degiro", DegiroConfig)
            except ImportError:
                # If BrokerFactory is not available, AuthenticationService should provide config
                pass

        self.set_credentials(credentials_manager)
        self.force = force
        self.is_maintenance_mode = False

    def set_credentials(self, credentials_manager: CredentialsManager):
        """
        Set credentials for API operations.
        This method is typically called by AuthenticationService.
        """
        if credentials_manager is not None:
            self.credentials_manager = credentials_manager
            self.api_client = TradingApi(credentials=self.credentials_manager.credentials)
            self.logger.debug("Credentials set for API client")
        elif self.credentials_manager is None:
            # Initialize with empty credentials if none provided
            self.credentials_manager = CredentialsManager()
            self.api_client = TradingApi(credentials=self.credentials_manager.credentials)
            self.logger.debug("Default credentials manager initialized")

    def connect(self):
        """Connect to the DeGiro API."""
        with requests_cache.enabled(
            cache_name=self.__cache_path,
            expire_after=timedelta(minutes=15),
            allowable_methods=["GET", "HEAD", "POST"],
            ignored_parameters=["oneTimePassword"],
        ):
            self.api_client.connect()

        if self.credentials_manager.credentials.int_account is None:
            int_account = self._get_int_account()
            self.credentials_manager.credentials.int_account = int_account
            self.api_client.credentials.int_account = int_account

    def check_connection(self) -> bool:
        """Check if the API client is connected."""
        if not self.force and self.degiro_config.offline_mode:
            raise DeGiroOfflineModeError("DEGIRO working in offline mode. No connection is allowed")

        is_connected = self.__check_connection__()
        if not is_connected:
            try:
                self.is_maintenance_mode = False
                self.connect()
            except MaintenanceError:
                # If we are in maintenance mode, we can still try to connect,
                # but we will not be able to get any data.
                self.logger.warning("DeGiro is in maintenance mode. Connection will not be established.")
                self.is_maintenance_mode = True
            except DeGiroConnectionError as error:
                raise error
            except ConnectionError:
                # Try to connect and validate the connection.
                # If we want more details, we can always call the connect method
                pass

        if self.is_maintenance_mode:
            return True

        return self.__check_connection__()

    def is_connected(self) -> bool:
        """Check if the API client is currently connected."""
        return self.api_client.connection_storage and self.api_client.connection_storage.connected.is_set()

    def __check_connection__(self) -> bool:
        """Internal connection check method."""
        return self.is_connected()

    def get_client(self) -> TradingApi:
        """
        Get the DeGiro API client for operations.
        Note: Connection should be established by AuthenticationService before calling this.
        """
        if not self.is_connected():
            self.logger.warning("API client is not connected. Ensure authentication is completed first.")
        return self.api_client

    def get_account_info(self) -> Any:
        """Get account information."""
        return self.get_client().get_account_info()

    def get_client_details(self) -> Any:
        """Get client details."""
        return self.get_client().get_client_details()

    def get_config(self) -> Any:
        """Get configuration details."""
        return self.get_client().get_config()

    def get_products_info(self, product_ids: List[str]) -> Any:
        """Get information about the specified products."""
        self.check_connection()
        product_ids = list(set(product_ids))
        products_info = self.api_client.get_products_info(product_list=product_ids, raw=True)
        return products_info["data"]

    def get_product_quotation(self, issue_id: str | None, isin: str, period: Interval, symbol: str) -> dict:
        daily_quotations = self._get_product_daily_quotation(issue_id=issue_id, isin=isin, period=period)
        if not daily_quotations:
            self.logger.error(f"Product Quotations for '{symbol}' ({issue_id}) / {period} not found")
            return {}
        last_key = next(reversed(daily_quotations))
        last_value = daily_quotations[last_key]
        last_quotation = self._get_product_last_quotation(issue_id, isin, symbol, last_value)
        return daily_quotations | last_quotation

    def _get_product_daily_quotation(self, issue_id: str | None, isin: str, period: Interval) -> dict:
        """
        Get the list of quotations for the provided product for the indicated interval.
        The response is a list of date-value pairs.
        """
        self.check_connection()

        chart = self._get_chart(issue_id=issue_id, isin=isin, period=period, resolution=Interval.P1D)
        if not chart:
            self.logger.warning(f"No chart found for {issue_id} / {period}")
            return {}

        quotes = {}
        for series in chart.series:
            if series.type != "time":
                continue

            init_date = LocalizationUtility.convert_string_to_date(series.times.split("/")[0])
            last_date = init_date

            data_frame = pl.DataFrame(data=series.data, orient="row")
            for row in data_frame.rows(named=True):
                delta_days = row["column_0"]
                current_date = init_date + timedelta(days=delta_days)

                # Fill missing days
                missing_days = (current_date - last_date).days
                if missing_days > 1:
                    last_known_value = quotes.get(LocalizationUtility.format_date_from_date(last_date), row["column_1"])
                    for day_offset in range(1, missing_days):
                        missing_date = last_date + timedelta(days=day_offset)
                        quotes[LocalizationUtility.format_date_from_date(missing_date)] = last_known_value

                # Add the current day's quotation
                current_date_str = LocalizationUtility.format_date_from_date(current_date)
                quotes[current_date_str] = row["column_1"]
                last_date = current_date

        return quotes

    def _get_product_last_quotation(self, issue_id: str, isin: str, symbol: str, default_quotation: str) -> dict:
        """
        Get the list of quotations for the provided product for the indicated interval.
        The response is a list of date-value pairs.
        """
        self.check_connection()

        chart = self._get_chart(issue_id=issue_id, isin=isin, period=Interval.P1D, resolution=Interval.P1D)
        if not chart:
            self.logger.warning(f"No chart found for {issue_id} / {Interval.P1D}")
            return {}

        quotes = {}
        for series in chart.series:
            if series.type != "time":
                continue

            current_date_str = LocalizationUtility.format_date_from_date(date.today())
            data_frame = pl.DataFrame(data=series.data, orient="row")
            if "column_1" in data_frame.columns:
                quotes[current_date_str] = data_frame["column_1"][-1]
            else:
                self.logger.warning(f"No daily quotation found for '{symbol}' ({issue_id} - {isin}) / {Interval.P1D}")
                quotes[current_date_str] = default_quotation

        return quotes

    @staticmethod
    def __is_chart_error_type(chart: Chart | None) -> bool:
        return chart.get("series", [{}])[0].get("type") == "error"

    def _get_chart(self, issue_id: str | None, isin: str, period: Interval, resolution: Interval) -> Chart | None:
        """Using the issue_id guarantees that we get exactly the product quotes. If it's not available, then we can use
        the isin. The issue_id may not be available if the product doesn't exist anymore.
        """
        chart = None
        if issue_id:
            chart = self.__get_chart(issue_id=issue_id, isin=None, period=period, resolution=resolution)

        if chart is None:
            chart = self.__get_chart(issue_id=None, isin=isin, period=period, resolution=resolution)

        return chart

    def __get_chart(
        self, issue_id: Optional[str], isin: Optional[str], period: Interval, resolution: Interval
    ) -> Chart | None:
        if not issue_id and not isin:
            raise ValueError("Either 'issue_id' or 'isin' must be provided")

        identifier_type = "isin" if isin else "issueid"
        identifier_value = isin if isin else issue_id

        user_token = self._get_user_token()
        chart_fetcher = ChartFetcher(user_token=user_token)
        chart_request = ChartRequest(
            culture="nl-NL",
            period=period,
            requestid="1",
            resolution=resolution,
            series=[
                f"{identifier_type}:{identifier_value}",
                f"price:{identifier_type}:{identifier_value}",
            ],
            tz=TIME_ZONE,
        )
        response = chart_fetcher.get_chart(chart_request=chart_request, raw=True)
        if not response or self.__is_chart_error_type(response):
            return None
        return Chart.model_validate(response)

    def _get_user_token(self) -> int:
        client_details = self.get_client_details()
        user_token = client_details["data"]["id"]

        return user_token

    def _get_int_account(self) -> int:
        client_details = self.get_client_details()
        int_account = client_details["data"]["intAccount"]

        return int_account

    def get_dividends_agenda(self, company_name: str, isin: str) -> dict | None:
        agenda = self.get_client().get_agenda(
            agenda_request=AgendaRequest(
                calendar_type=CalendarType.DIVIDEND_CALENDAR,
                start_date=datetime.now(),
                # DEGIRO API seems to limit the agenda to 6 months in the future
                #  even with that limitation doesn't show the whole agenda
                end_date=datetime.now() + timedelta(days=180),
                offset=0,
                limit=25,
                isin=isin,
            ),
            raw=True,
        )

        forecasted_dividends = [item for item in agenda["items"] if item.get("isin") == isin]
        if len(forecasted_dividends) > 1:
            self.logger.warning(
                f"Multiple forecasted dividends found for '{company_name}' ({isin}). " + "Using the first one."
            )

        return forecasted_dividends[0] if forecasted_dividends else None

    def get_session_id(self) -> str:
        config_table = self.get_config()
        return config_table["sessionId"]
