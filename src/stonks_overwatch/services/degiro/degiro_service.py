import logging
import os
from datetime import date, timedelta
from typing import Any, List, Optional

import polars as pl
import requests_cache
from degiro_connector.quotecast.models.chart import ChartRequest, Interval
from degiro_connector.quotecast.tools.chart_fetcher import ChartFetcher
from degiro_connector.trading.api import API as TradingApi  # noqa: N811
from degiro_connector.trading.models.credentials import Credentials

import settings
from stonks_overwatch.config.degiro_config import DegiroConfig
from stonks_overwatch.utils.localization import LocalizationUtility
from stonks_overwatch.utils.singleton import singleton


class CredentialsManager:
    """Manages the credentials for the DeGiro API."""

    def __init__(self, credentials: Optional[Credentials] = None):
        degiro_config = DegiroConfig.default()
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
        if (not self.credentials or not hasattr(self.credentials, 'username')
                or not hasattr(self.credentials, 'password')):
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
    logger = logging.getLogger("stocks_portfolio.degiro_service")
    api_client: TradingApi = None
    credentials_manager: Optional[CredentialsManager] = None

    __cache_path = os.path.join(settings.TEMP_DIR, 'http_request.cache')

    def __init__(self, credentials_manager: Optional[CredentialsManager] = None):
        self.set_credentials(credentials_manager)

    def set_credentials(self, credentials_manager: CredentialsManager):
        self.credentials_manager = credentials_manager or CredentialsManager()
        self.api_client = TradingApi(credentials=self.credentials_manager.credentials)

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
        is_connected = self.__check_connection__()
        if not is_connected:
            try:
                self.connect()
            except ConnectionError:
                # Just try to connect and validate the connection.
                # If we want more details we can always call the connect method
                pass

        return self.__check_connection__()

    def __check_connection__(self) -> bool:
        return self.api_client.connection_storage and self.api_client.connection_storage.connected.is_set()

    def get_client(self) -> TradingApi:
        self.check_connection()
        return self.api_client

    def get_account_info(self) -> Any:
        """Get account information."""
        self.check_connection()
        return self.api_client.get_account_info()

    def get_client_details(self) -> Any:
        """Get client details."""
        self.check_connection()
        return self.api_client.get_client_details()

    def get_config(self) -> Any:
        """Get configuration details."""
        self.check_connection()
        return self.api_client.get_config()

    def get_products_info(self, product_ids: List[str]) -> Any:
        """Get information about the specified products."""
        self.check_connection()
        product_ids = list(set(product_ids))
        products_info = self.api_client.get_products_info(product_list=product_ids, raw=True)
        return products_info["data"]

    def get_product_quotation(self, issue_id: str, period: Interval, symbol: str) -> dict:
        daily_quotations = self._get_product_daily_quotation(issue_id, period)
        if not daily_quotations:
            self.logger.error(f"Product Quotations for '{symbol}'({issue_id}) / {period} not found")
            return {}
        last_key = next(reversed(daily_quotations))
        last_value = daily_quotations[last_key]
        last_quotation = self._get_product_last_quotation(issue_id, symbol, last_value)
        return daily_quotations | last_quotation

    def _get_product_daily_quotation(self, issue_id: str, period: Interval) -> dict:
        """
        Get the list of quotations for the provided product for the indicated interval.
        The response is a list of date-value pairs.
        """
        self.check_connection()

        chart = self._get_chart(issue_id, period, Interval.P1D)
        if not chart:
            self.logger.warning(f"No chart found for {issue_id} / {period}")
            return {}

        quotes = {}
        for series in chart.series:
            if series.type != "time":
                continue

            init_date = LocalizationUtility.convert_string_to_date(series.times.split('/')[0])
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

    def _get_product_last_quotation(self, issue_id: str, symbol: str, default_quotation: str) -> dict:
        """
        Get the list of quotations for the provided product for the indicated interval.
        The response is a list of date-value pairs.
        """
        self.check_connection()

        chart = self._get_chart(issue_id, Interval.P1D, Interval.PT15M)
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
                self.logger.warning(f"No daily quotation found for '{symbol}'({issue_id}) / {Interval.P1D}")
                quotes[current_date_str] = default_quotation

        return quotes

    def _get_chart(self, issue_id: str, period: Interval, resolution: Interval):
        user_token = self._get_user_token()

        chart_fetcher = ChartFetcher(user_token=user_token)
        chart_request = ChartRequest(
            culture="nl-NL",
            period=period,
            requestid="1",
            resolution=resolution,
            series=[
                f"issueid:{issue_id}",
                f"price:issueid:{issue_id}",
            ],
            tz="Europe/Amsterdam",
        )
        return chart_fetcher.get_chart(chart_request=chart_request, raw=False)

    def _get_user_token(self) -> int:
        client_details = self.get_client_details()
        user_token = client_details["data"]["id"]

        return user_token

    def _get_int_account(self) -> int:
        client_details = self.get_client_details()
        int_account = client_details["data"]["intAccount"]

        return int_account

    def get_session_id(self) -> str:
        config_table = self.get_config()
        return config_table['sessionId']
