import json
import logging

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.trading_pb2 import Credentials, ProductsInfo

from degiro.utils.single_instance_metaclass import SingleInstanceMetaClass

# TODO: A singleton is nice, but doesn't allow for multiple users
class DeGiro(metaclass=SingleInstanceMetaClass):
    trading_api = None
    clientId = None
    sessionId = None

    def __init__(self):
        # SETUP LOGGING LEVEL
        logging.basicConfig(level=logging.INFO)

        # SETUP CONFIG DICT
        with open('config/config.json') as config_file:
            config_dict = json.load(config_file)

        # SETUP CREDENTIALS
        username = config_dict['username']
        password = config_dict['password']
        int_account = config_dict['int_account']
        # FIXME: Using Totp is convenient, but not secure
        totp_secret_key = config_dict['totp_secret_key']
        credentials = Credentials(
            int_account=int_account,
            username=username,
            password=password,
            totp_secret_key=totp_secret_key,
        )

        # SETUP TRADING API
        self.trading_api = TradingAPI(credentials=credentials)

        # CONNECT
        self.trading_api.connect()
    
    @staticmethod
    def get_client() -> TradingAPI:
        degiro = DeGiro()

        config_table = degiro.trading_api.get_config()

        degiro.clientId = config_table['clientId']
        degiro.sessionId = config_table['sessionId']

        return degiro.trading_api

    @staticmethod
    def get_account_info():
        return DeGiro.get_client().get_account_info()

    @staticmethod
    def get_client_details():
        # FETCH CONFIG TABLE
        client_details_table = DeGiro.get_client().get_client_details()

        # EXTRACT DATA
        int_account = client_details_table['data']['intAccount']
        user_token = client_details_table['data']['id']
        client_details_pretty = json.dumps(
            client_details_table,
            sort_keys=True,
            indent=4,
        )

        return client_details_table
    
    @staticmethod
    def get_config():
        config_table = DeGiro.get_client().get_config()

        return config_table

    @staticmethod
    def get_products_info(products_ids):
        products_ids = list(set(products_ids))

        # SETUP REQUEST
        request = ProductsInfo.Request()
        request.products.extend(products_ids)

        # FETCH DATA
        products_info = DeGiro.get_client().get_products_info(
            request=request,
            raw=True,
        )

        return products_info['data']