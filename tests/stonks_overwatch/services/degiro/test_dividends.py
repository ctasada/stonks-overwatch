import json
import pathlib

from isodate import parse_date, parse_datetime

from stonks_overwatch.config.degiro_credentials import DegiroCredentials
from stonks_overwatch.services.brokers.degiro.client.degiro_client import CredentialsManager
from stonks_overwatch.services.brokers.degiro.repositories.models import (
    DeGiroCashMovements,
    DeGiroProductInfo,
    DeGiroProductQuotation,
    DeGiroUpcomingPayments,
)
from stonks_overwatch.services.brokers.degiro.services.account_service import AccountOverviewService
from stonks_overwatch.services.brokers.degiro.services.currency_service import CurrencyConverterService
from stonks_overwatch.services.brokers.degiro.services.dividend_service import DividendsService
from stonks_overwatch.services.brokers.degiro.services.portfolio_service import PortfolioService
from stonks_overwatch.services.models import DividendType
from stonks_overwatch.utils.core.localization import LocalizationUtility
from tests.stonks_overwatch.fixtures import TestDeGiroService

import pook
import pytest
from django.test import TestCase


@pytest.mark.django_db
class TestDividendsService(TestCase):
    def setUp(self):
        self.created_objects = {}
        self.fixture_cash_movements_repository()
        self.fixture_product_info_repository()
        self.fixture_product_quotation_repository()
        self.fixture_dividends_upcoming_repository()
        self.degiro_service = TestDeGiroService(CredentialsManager(self.fixture_credentials()))

        self.account_overview = AccountOverviewService()
        self.currency_service = CurrencyConverterService()
        self.portfolio_service = PortfolioService(self.degiro_service)

        self.dividends_service = DividendsService(
            account_overview=self.account_overview,
            currency_service=self.currency_service,
            portfolio_service=self.portfolio_service,
            degiro_service=self.degiro_service,
        )

    def fixture_cash_movements_repository(self):
        data_file = pathlib.Path("tests/resources/stonks_overwatch/repositories/degiro/cash_movements_data.json")

        with open(data_file, "r") as file:
            data = json.load(file)

        for key, value in data.items():
            value["date"] = parse_datetime(value["date"])
            value["value_date"] = parse_datetime(value["value_date"])

            # Create and save the CashMovements object
            obj = DeGiroCashMovements.objects.create(**value)
            self.created_objects[key] = obj

    def fixture_product_info_repository(self):
        data_file = pathlib.Path("tests/resources/stonks_overwatch/repositories/degiro/product_info_data.json")

        with open(data_file, "r") as file:
            data = json.load(file)

        for key, value in data.items():
            # Create and save the ProductInfo object
            obj = DeGiroProductInfo.objects.create(**value)
            self.created_objects[key] = obj

    def fixture_product_quotation_repository(self):
        data_file = pathlib.Path("tests/resources/stonks_overwatch/repositories/degiro/product_quotations_data.json")

        with open(data_file, "r") as file:
            data = json.load(file)

        self.created_objects = {}
        for key, value in data.items():
            # Create and save the ProductQuotation object
            obj = DeGiroProductQuotation.objects.create(
                id=key, interval="P1D", last_import=LocalizationUtility.now(), quotations=value
            )
            self.created_objects[key] = obj

    def fixture_dividends_upcoming_repository(self):
        data_file = pathlib.Path("tests/resources/stonks_overwatch/repositories/degiro/dividends_upcoming_data.json")

        with open(data_file, "r") as file:
            data = json.load(file)

        for key, value in data.items():
            # Create and save the ProductInfo object
            value["pay_date"] = parse_date(value["pay_date"])
            obj = DeGiroUpcomingPayments.objects.create(**value)
            self.created_objects[key] = obj

    def fixture_credentials(self):
        return DegiroCredentials(
            username="testuser",
            password="testpassword",
            int_account=987654,
            totp_secret_key="ABCDEFGHIJKLMNOP",
            one_time_password=123456,
        )

    def tearDown(self):
        # Clean up the created objects
        for obj in self.created_objects.values():
            obj.delete()

    def test_get_dividends(self):
        dividends = self.dividends_service._get_dividends()
        assert len(dividends) == 1

        assert dividends[0].payment_date_as_string() == "2021-03-12"
        assert dividends[0].payment_time_as_string() == "08:16:38"
        assert dividends[0].stock_name == "Microsoft Corp"
        assert dividends[0].stock_symbol == "MSFT"
        assert dividends[0].currency == "EUR"
        assert dividends[0].amount == pytest.approx(7.52, rel=1e-2)
        assert dividends[0].taxes == pytest.approx(0.0, rel=1e-2)
        assert dividends[0].formated_change() == "€ 7.53"
        assert dividends[0].dividend_type == DividendType.PAID

    @pook.on
    def test_get_upcoming_dividends(self):
        upcoming_dividends = self.dividends_service._get_upcoming_dividends()

        assert len(upcoming_dividends) == 1

        assert upcoming_dividends[0].payment_date_as_string() == "2025-06-12"
        assert upcoming_dividends[0].stock_name == "Microsoft Corp"
        assert upcoming_dividends[0].stock_symbol == "MSFT"
        assert upcoming_dividends[0].currency == "EUR"
        assert upcoming_dividends[0].amount == pytest.approx(18.59, rel=1e-2)
        assert upcoming_dividends[0].taxes == pytest.approx(2.78, rel=1e-2)
        assert upcoming_dividends[0].formated_change() == "€ 15.81"
        assert upcoming_dividends[0].dividend_type == DividendType.ANNOUNCED
