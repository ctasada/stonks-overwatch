from django.views import View
from django.shortcuts import render
import pycountry

from degiro.models.user import UserModel

import json

class User(View):
    def __init__(self):
        self.user = UserModel()

    def get(self, request):
        clientDetails = self.user.getDetails()

        context = {
            "username": clientDetails['username'],
            "clientRole": clientDetails['clientRole'].capitalize(),
            "fullName": clientDetails['displayName'],
            "dateOfBirth": clientDetails['firstContact']['dateOfBirth'],
            "nationality": pycountry.languages.get(alpha_2=clientDetails['firstContact']['nationality']).name,
        }

        return render(request, 'user.html', context)
