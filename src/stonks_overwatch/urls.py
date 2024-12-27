from django.urls import path
from django.views.generic import RedirectView

from stonks_overwatch.views.account_overview import AccountOverview
from stonks_overwatch.views.dashboard import Dashboard
from stonks_overwatch.views.deposits import Deposits
from stonks_overwatch.views.diversification import Diversification
from stonks_overwatch.views.dividends import Dividends
from stonks_overwatch.views.fees import Fees
from stonks_overwatch.views.login import Login
from stonks_overwatch.views.portfolio import Portfolio
from stonks_overwatch.views.transactions import Transactions

urlpatterns = [
    path("", RedirectView.as_view(url="dashboard")),
    path("login", Login.as_view(), name="login"),
    path("account_overview", AccountOverview.as_view(), name="account_overview"),
    path("dashboard", Dashboard.as_view(), name="dashboard"),
    path("deposits", Deposits.as_view(), name="deposits"),
    path("diversification", Diversification.as_view(), name="diversification"),
    path("dividends", Dividends.as_view(), name="dividends"),
    path("fees", Fees.as_view(), name="fees"),
    path("portfolio", Portfolio.as_view(), name="portfolio"),
    path("transactions", Transactions.as_view(), name="transactions"),
]
