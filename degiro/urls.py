from django.urls import path
from degiro.views.dashboard import Dashboard
from django.views.generic import RedirectView
from degiro.views.portfolio import Portfolio
from degiro.views.transactions import Transactions
from degiro.views.user import User

from . import views

urlpatterns = [
    path('', RedirectView.as_view(url='dashboard')),
    path('dashboard', Dashboard.as_view(), name='dashboard'),
    path('portfolio', Portfolio.as_view(), name='portfolio'),
    path('transactions', Transactions.as_view(), name='transactions'),
    path('user', User.as_view(), name='user'),
]