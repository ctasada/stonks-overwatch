"""URL configuration for stocks_portfolio project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/

Examples
--------
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))

"""

from django.urls import path, re_path

from stonks_overwatch.views.account_overview import AccountOverview
from stonks_overwatch.views.asset_logos import AssetLogoView
from stonks_overwatch.views.broker_login import BrokerLogin
from stonks_overwatch.views.configuration import ConfigurationView
from stonks_overwatch.views.dashboard import Dashboard
from stonks_overwatch.views.deposits import Deposits
from stonks_overwatch.views.diversification import Diversification
from stonks_overwatch.views.dividends import Dividends
from stonks_overwatch.views.fees import Fees
from stonks_overwatch.views.login import Login
from stonks_overwatch.views.portfolio import Portfolio
from stonks_overwatch.views.release_notes import ReleaseNotesView
from stonks_overwatch.views.root_redirect import RootRedirectView
from stonks_overwatch.views.settings import SettingsView
from stonks_overwatch.views.static import RootStaticFileView
from stonks_overwatch.views.transactions import Transactions

urlpatterns = [
    path("", RootRedirectView.as_view(), name="root"),
    path("login", Login.as_view(), name="login"),
    path("login/<str:broker_name>", BrokerLogin.as_view(), name="broker_login"),
    path("account_overview", AccountOverview.as_view(), name="account_overview"),
    path("dashboard", Dashboard.as_view(), name="dashboard"),
    path("deposits", Deposits.as_view(), name="deposits"),
    path("diversification", Diversification.as_view(), name="diversification"),
    path("dividends", Dividends.as_view(), name="dividends"),
    path("fees", Fees.as_view(), name="fees"),
    path("portfolio", Portfolio.as_view(), name="portfolio"),
    path("transactions", Transactions.as_view(), name="transactions"),
    path("configuration", ConfigurationView.as_view(), name="configuration"),
    path("release_notes", ReleaseNotesView.as_view(), name="release_notes"),
    path("settings", SettingsView.as_view(), name="settings"),
    path("assets/<str:product_type>/<str:symbol>", AssetLogoView.as_view(), name="asset_logo"),
    re_path(r"^(favicon\.ico|apple-touch-icon\.png|apple-touch-icon-precomposed\.png)$", RootStaticFileView.as_view()),
]
