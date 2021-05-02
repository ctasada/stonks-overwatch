import json
import logging

from trading.api import API as TradingAPI
from trading.pb.trading_pb2 import Credentials

class DeGiro():
    def __init__(self):
        # SETUP LOGGING LEVEL
        logging.basicConfig(level=logging.DEBUG)

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
    
    def getClient(self) -> TradingAPI:
        return self.trading_api

    def _get_account_info(self):
        return self.trading_api.get_account_info()

    def _get_client_details(self):
        # FETCH CONFIG TABLE
        client_details_table = self.trading_api.get_client_details()

        # EXTRACT DATA
        int_account = client_details_table['data']['intAccount']
        user_token = client_details_table['data']['id']
        client_details_pretty = json.dumps(
            client_details_table,
            sort_keys=True,
            indent=4,
        )

        return client_details_table
    
    def _get_config(self):
        config_table = self.trading_api.get_config()

        return config_table