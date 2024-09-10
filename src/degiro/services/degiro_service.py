import logging
from datetime import timedelta

import polars as pl
import requests_cache
from degiro_connector.quotecast.models.chart import ChartRequest, Interval
from degiro_connector.quotecast.tools.chart_fetcher import ChartFetcher
from degiro_connector.trading.api import API as TradigApi  # noqa: N811
from degiro_connector.trading.models.credentials import Credentials

from degiro.config.degiro_config import DegiroConfig


class DeGiroService():
    api_client = None

    def __init__(self):
        # SETUP LOGGING LEVEL
        logging.basicConfig(level=logging.INFO)

        degiro_config = DegiroConfig.default()
        degiro_credentials = degiro_config.credentials
        # SETUP CREDENTIALS
        credentials = Credentials(
            int_account=degiro_credentials.int_account,
            username=degiro_credentials.username,
            password=degiro_credentials.password,
            # FIXME: Using Totp is convenient, but not secure
            totp_secret_key=degiro_credentials.totp_secret_key,
        )
        # SETUP TRADING API
        self.api_client = TradigApi(credentials=credentials)

    def connect(self):
        # CONNECT
        with requests_cache.enabled(
            expire_after=timedelta(minutes=15),
            allowable_methods=["GET", "HEAD", "POST"],
            ignored_parameters=["oneTimePassword"],
        ):
            self.api_client.connect()

    def is_connected(self) -> bool:
        return self.api_client.connection_storage and self.api_client.connection_storage.connected.isSet()

    def __check_connection__(self):
        if not self.is_connected():
            self.connect()

    def get_client(self) -> TradigApi:
        self.__check_connection__()
        return self.api_client

    def get_account_info(self):
        self.__check_connection__()
        return self.api_client.get_account_info()

    def get_client_details(self):
        self.__check_connection__()
        client_details_table = self.api_client.get_client_details()

        return client_details_table

    def get_config(self):
        config_table = self.api_client.get_config()

        return config_table

    def get_products_info(self, products_ids):
        self.__check_connection__()
        products_ids = list(set(products_ids))

        # FETCH DATA
        products_info = self.api_client.get_products_info(
            product_list=products_ids,
            raw=True,
        )

        return products_info["data"]

    def get_product_quotation(self, issueid, period: Interval) -> list:
        """Get the list of quotations for the provided product for the indicated Interval.

        ### Parameters
            * issueid
                - ID representing the product. Should be 'vwdIdSecondary' or 'vwdId'
            * interval:
                - Time period from today to the past to retrieve the quotations
        ### Returns
            list: List with the quotations
        """
        # Retrieve user_token
        client_details_table = self.get_client_details()
        user_token = client_details_table["data"]["id"]

        chart_fetcher = ChartFetcher(user_token=user_token)
        chart_request = ChartRequest(
            culture="nl-NL",
            period=period,
            requestid="1",
            resolution=Interval.P1D,
            series=[
                f"issueid:{issueid}",
                f"price:issueid:{issueid}",
            ],
            tz="Europe/Amsterdam",
        )
        chart = chart_fetcher.get_chart(
            chart_request=chart_request,
            raw=False,
        )

        quotes = None
        for series in chart.series:
            if series.type == "time":
                # 'column_0' is the position, and 'column_1' is the value.
                data_frame = pl.DataFrame(data=series.data, orient="row")
                quotes = []
                i = 1
                for row in data_frame.rows(named=True):
                    # Some values are missing, lets fill them re-using the last know value
                    if row["column_0"] != i:
                        for _j in range(i, row["column_0"]):
                            # Even the first entry may be empty, in that case we need to use the provided value
                            value = quotes[-1] if len(quotes) > 0 else row["column_1"]
                            quotes.append(value)
                            i += 1
                    quotes.append(row["column_1"])
                    i += 1

        return quotes
