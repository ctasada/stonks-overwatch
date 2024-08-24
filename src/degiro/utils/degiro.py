from datetime import timedelta
import logging
import requests_cache

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials
from degiro.config.degiro_config import DegiroConfig
from degiro.utils.single_instance_metaclass import SingleInstanceMetaClass


# TODO: A singleton is nice, but doesn't allow for multiple users
class DeGiro(metaclass=SingleInstanceMetaClass):
    apiClient = None

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
        self.apiClient = TradingAPI(credentials=credentials)

    @staticmethod
    def get_client() -> TradingAPI:
        degiro = DeGiro()

        # CONNECT
        with requests_cache.enabled(
            expire_after=timedelta(minutes=15),
            allowable_methods=["GET", "HEAD", "POST"],
            ignored_parameters=["oneTimePassword"],
        ):
            degiro.apiClient.connect()

        return degiro.apiClient

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
