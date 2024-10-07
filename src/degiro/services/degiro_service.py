from datetime import timedelta
from typing import Any, List, Optional

import polars as pl
import requests_cache
from degiro_connector.quotecast.models.chart import ChartRequest, Interval
from degiro_connector.quotecast.tools.chart_fetcher import ChartFetcher
from degiro_connector.trading.api import API as TradingApi  # noqa: N811
from degiro_connector.trading.models.credentials import Credentials

from degiro.config.degiro_config import DegiroConfig
from degiro.utils.localization import LocalizationUtility


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


class DeGiroService:
    def __init__(self, credentials_manager: Optional[CredentialsManager] = None):
        self.credentials_manager = credentials_manager or CredentialsManager()
        self.api_client = TradingApi(credentials=self.credentials_manager.credentials)

    def connect(self):
        """Connect to the DeGiro API."""
        with requests_cache.enabled(
            expire_after=timedelta(minutes=15),
            allowable_methods=["GET", "HEAD", "POST"],
            ignored_parameters=["oneTimePassword"],
        ):
            self.api_client.connect()

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

    def get_product_quotation(self, issue_id: str, period: Interval) -> dict:
        """Get the list of quotations for the provided product for the indicated interval.
        The response is a list of date-value pairs.
        """
        self.check_connection()

        client_details = self.get_client_details()
        user_token = client_details["data"]["id"]

        chart_fetcher = ChartFetcher(user_token=user_token)
        chart_request = ChartRequest(
            culture="nl-NL",
            period=period,
            requestid="1",
            resolution=Interval.P1D,
            series=[
                f"issueid:{issue_id}",
                f"price:issueid:{issue_id}",
            ],
            tz="Europe/Amsterdam",
        )
        chart = chart_fetcher.get_chart(chart_request=chart_request, raw=False)

        quotes = {}
        for series in chart.series:
            if series.type == "time":
                init_date = series.times.split('/')[0]
                last_date = LocalizationUtility.convert_string_to_date(init_date)
                data_frame = pl.DataFrame(data=series.data, orient="row")
                for row in data_frame.rows(named=True):
                    delta_days = row["column_0"]
                    current_date = LocalizationUtility.convert_string_to_date(init_date) + timedelta(days=delta_days)

                    if (current_date - last_date).days > 1:
                        last_date_str = LocalizationUtility.format_date_from_date(last_date)
                        for missing_day in (range(1, (current_date - last_date).days)):
                            missing_day_str = LocalizationUtility.format_date_from_date(
                                last_date + timedelta(days=missing_day)
                            )
                            # Sometimes the first value is skipped, so we need to look at the current one
                            if last_date_str in quotes:
                                last_known_value = quotes[last_date_str]
                            else:
                                last_known_value = row["column_1"]
                            quotes[missing_day_str] = last_known_value

                    current_date_str = LocalizationUtility.format_date_from_date(current_date)
                    quotes[current_date_str] = row["column_1"]
                    last_date = current_date

        return quotes
