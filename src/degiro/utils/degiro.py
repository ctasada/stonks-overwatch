import logging
from datetime import timedelta

import polars as pl
import requests_cache
from degiro_connector.quotecast.models.chart import ChartRequest, Interval
from degiro_connector.quotecast.tools.chart_fetcher import ChartFetcher
from degiro_connector.trading.api import API as TRADING_API
from degiro_connector.trading.models.credentials import Credentials

from degiro.config.degiro_config import DegiroConfig
from degiro.utils.single_instance_metaclass import SingleInstanceMetaClass


# TODO: A singleton is nice, but doesn't allow for multiple users
class DeGiro(metaclass=SingleInstanceMetaClass):
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
        self.api_client = TRADING_API(credentials=credentials)

    @staticmethod
    def get_client() -> TRADING_API:
        degiro = DeGiro()

        # CONNECT
        with requests_cache.enabled(
            expire_after=timedelta(minutes=15),
            allowable_methods=["GET", "HEAD", "POST"],
            ignored_parameters=["oneTimePassword"],
        ):
            degiro.api_client.connect()

        return degiro.api_client

    @staticmethod
    def get_account_info():
        return DeGiro.get_client().get_account_info()

    @staticmethod
    def get_client_details():
        # FETCH CONFIG TABLE
        client_details_table = DeGiro.get_client().get_client_details()

        return client_details_table

    @staticmethod
    def get_config():
        config_table = DeGiro.get_client().get_config()

        return config_table

    @staticmethod
    def get_products_info(products_ids):
        products_ids = list(set(products_ids))

        # FETCH DATA
        products_info = DeGiro.get_client().get_products_info(
            product_list=products_ids,
            raw=True,
        )

        return products_info["data"]

    @staticmethod
    def get_product_quotation(issueid, period: Interval) -> list:
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
        client_details_table = DeGiro.get_client_details()
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
