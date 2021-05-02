from django.http import HttpResponse
from django.http import JsonResponse
from django.views import View

from degiro.utils.degiro import DeGiro

import json

class Account(View):
    def __init__(self):
        self.deGiro = DeGiro()

    def get(self, request):

        # info = self._get_client_details()
        # info = self._get_account()
        info = self.deGiro._get_config()

        return JsonResponse(info)
