from django.urls import path
from degiro.views.dashboard import Dashboard
from django.views.generic import RedirectView
from degiro.views.portfolio import Portfolio
from degiro.views.deposits import Deposits
from degiro.views.dividends import Dividends
from degiro.views.transactions import Transactions
from degiro.views.account_overview import AccountOverview


urlpatterns = [
    path("", RedirectView.as_view(url="dashboard")),
    path("dashboard", Dashboard.as_view(), name="dashboard"),
    path("portfolio", Portfolio.as_view(), name="portfolio"),
    path("dividends", Dividends.as_view(), name="dividends"),
    path("transactions", Transactions.as_view(), name="transactions"),
    path("deposits", Deposits.as_view(), name="deposits"),
    path("account_overview", AccountOverview.as_view(), name="account_overview"),
]
