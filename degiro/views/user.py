from django.http import HttpResponse
from django.http import JsonResponse
from django.views import View
from django.shortcuts import render

from degiro.utils.degiro import DeGiro

import json

class User(View):
    def __init__(self):
        self.deGiro = DeGiro()

    def get(self, request):

        return render(request, 'user.html', {})
