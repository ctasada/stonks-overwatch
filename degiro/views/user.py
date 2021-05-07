from django.http import HttpResponse
from django.http import JsonResponse
from django.views import View
from django.shortcuts import render
import pycountry

from degiro.utils.degiro import DeGiro

import json

class User(View):
    def __init__(self):
        self.deGiro = DeGiro()

    def get(self, request):
        accountInfo = self.deGiro.get_account_info()
        clientDetails = self.deGiro.get_client_details()
        # info = self.deGiro._get_config()
        # return JsonResponse(info)

        print(clientDetails)

        context = {
            "username": clientDetails['data']['username'],
            "clientRole": clientDetails['data']['clientRole'].capitalize(),
            "fullName": clientDetails['data']['displayName'],
            "dateOfBirth": clientDetails['data']['firstContact']['dateOfBirth'],
            "nationality": pycountry.countries.get(alpha_2=clientDetails['data']['firstContact']['nationality']).name,
        }

        return render(request, 'user.html', context)
