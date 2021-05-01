from django.urls import path
from degiro.views.account import Account

from . import views

urlpatterns = [
    path('account', Account.as_view()),
]