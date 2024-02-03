from django.views import View
from django.shortcuts import render
import pycountry

from degiro.integration.user import UserData

import json

class User(View):
    def __init__(self):
        self.user = UserData()

    def get(self, request):
        clientDetails = self.user.get_details()

        context = {
            "username": clientDetails['username'],
            "clientRole": clientDetails['clientRole'].capitalize(),
            "fullName": clientDetails['displayName'],
            "dateOfBirth": clientDetails['firstContact']['dateOfBirth'],
            "nationality": pycountry.languages.get(alpha_2=clientDetails['firstContact']['nationality']).name,
            "email": clientDetails['email'],
            "language": pycountry.languages.get(alpha_2=clientDetails['language']).name,
            "displayLanguage": pycountry.languages.get(alpha_2=clientDetails['displayLanguage']).name,
        }

        return render(request, 'user.html', context)
