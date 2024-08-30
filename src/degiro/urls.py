from django.urls import path
from django.views.generic import RedirectView

from degiro.views.account_overview import AccountOverview
from degiro.views.dashboard import Dashboard
from degiro.views.deposits import Deposits
from degiro.views.dividends import Dividends
from degiro.views.fees import Fees
from degiro.views.portfolio import Portfolio
from degiro.views.transactions import Transactions

urlpatterns = [
    path("", RedirectView.as_view(url="dashboard")),
    path("account_overview", AccountOverview.as_view(), name="account_overview"),
    path("dashboard", Dashboard.as_view(), name="dashboard"),
    path("deposits", Deposits.as_view(), name="deposits"),
    path("dividends", Dividends.as_view(), name="dividends"),
    path("fees", Fees.as_view(), name="fees"),
    path("portfolio", Portfolio.as_view(), name="portfolio"),
    path("transactions", Transactions.as_view(), name="transactions"),
]
