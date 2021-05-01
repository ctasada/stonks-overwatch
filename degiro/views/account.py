from django.http import HttpResponse
from django.http import JsonResponse
from django.views import View

import json
import logging

from trading.api import API as TradingAPI
from trading.pb.trading_pb2 import Credentials

class Account(View):
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

    def get(self, request):

        info = self._get_client_details()

        return JsonResponse(info)

    def _get_account(self):
        # FETCH DATA
        account_info_table = self.trading_api.get_account_info()

        # DISPLAY DATA
        account_info_pretty = json.dumps(account_info_table, sort_keys=True, indent=4)
        
        return account_info_table

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