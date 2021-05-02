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
        one_time_password = config_dict['one_time_password']
        credentials = Credentials(
            int_account=int_account,
            username=username,
            password=password,
            one_time_password=one_time_password,
        )

        # SETUP TRADING API
        self.trading_api = TradingAPI(credentials=credentials)

        # CONNECT
        self.trading_api.connect()
    
    def getClient(self) -> TradingAPI:
        return self.trading_api
