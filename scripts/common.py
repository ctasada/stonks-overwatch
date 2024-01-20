# IMPORTATIONS
import datetime
import json
import logging

from datetime import date

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials
from degiro_connector.trading.models.account import OverviewRequest

# SETUP LOGGING LEVEL
logging.basicConfig(level=logging.DEBUG)

def connectToDegiro():
    # SETUP CONFIG DICT
    with open('./config/config.json') as config_file:
        config_dict = json.load(config_file)

    # SETUP CREDENTIALS
    int_account = config_dict['int_account']
    username = config_dict['username']
    password = config_dict['password']
    totp_secret_key = config_dict['totp_secret_key']
    credentials = Credentials(
        int_account=int_account,
        username=username,
        password=password,
        totp_secret_key=totp_secret_key,
    )

    # SETUP TRADING API
    trading_api = TradingAPI(credentials=credentials)

    # CONNECT
    trading_api.connect()

    return trading_api
