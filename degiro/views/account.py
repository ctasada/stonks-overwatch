from django.http import HttpResponse
from django.http import JsonResponse
from django.views import View

from degiro.utils.degiro import DeGiro

import json

class Account(View):
    def __init__(self):
        deGiro = DeGiro()

        self.trading_api = deGiro.getClient()

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