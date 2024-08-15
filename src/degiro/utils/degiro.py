from datetime import timedelta
import json
import logging
import requests_cache

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials
from degiro.utils.single_instance_metaclass import SingleInstanceMetaClass


# TODO: A singleton is nice, but doesn't allow for multiple users
class DeGiro(metaclass=SingleInstanceMetaClass):
    apiClient = None

    def __init__(self):
        # SETUP LOGGING LEVEL
        logging.basicConfig(level=logging.INFO)

        # SETUP CONFIG DICT
        with open("config/config.json") as config_file:
            config_dict = json.load(config_file)

        # SETUP CREDENTIALS
        username = config_dict["username"]
        password = config_dict["password"]
        int_account = config_dict["int_account"]
        # FIXME: Using Totp is convenient, but not secure
        totp_secret_key = config_dict["totp_secret_key"]
        credentials = Credentials(
            int_account=int_account,
            username=username,
            password=password,
            totp_secret_key=totp_secret_key,
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

        # EXTRACT DATA
        # int_account = client_details_table["data"]["intAccount"]
        # user_token = client_details_table["data"]["id"]
        # client_details_pretty = json.dumps(
        #     client_details_table,
        #     sort_keys=True,
        #     indent=4,
        # )

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
