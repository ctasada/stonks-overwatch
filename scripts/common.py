# IMPORTATIONS
import json
import logging

from degiro_connector.trading.api import API as TradingAPI
from degiro_connector.trading.models.credentials import Credentials

# SETUP LOGGING LEVEL
logging.basicConfig(level=logging.DEBUG)


def connectToDegiro():
    # SETUP CONFIG DICT
    with open('./config/config.json') as config_file:
        config_dict = json.load(config_file)

    degiro_credentials = config_dict['degiro']['credentials']

    # SETUP CREDENTIALS
    int_account = degiro_credentials['int_account']
    username = degiro_credentials['username']
    password = degiro_credentials['password']
    totp_secret_key = degiro_credentials['totp_secret_key']
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
