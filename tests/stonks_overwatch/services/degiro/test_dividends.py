import json
import pathlib
import re
from unittest.mock import patch

import requests
import requests_mock
from degiro_connector.core.constants import urls
from django.test import TestCase
from isodate import parse_datetime

import pytest
from stonks_overwatch.config import DegiroCredentials
from stonks_overwatch.repositories.degiro.models import DeGiroCashMovements, DeGiroProductInfo
from stonks_overwatch.services.degiro.account_overview import AccountOverviewService
from stonks_overwatch.services.degiro.degiro_service import CredentialsManager
from stonks_overwatch.services.degiro.dividends import DividendsService
from tests.stonks_overwatch.fixtures import TestDeGiroService


@pytest.mark.django_db
class TestDividendsService(TestCase):
    def setUp(self):
        self.created_objects = {}
        self.fixture_cash_movements_repository()
        self.fixture_product_info_repository()
        self.degiro_service = TestDeGiroService(CredentialsManager(self.fixture_credentials()))

        self.account_overview = AccountOverviewService()

        self.dividends_service = DividendsService(
            account_overview=self.account_overview,
            degiro_service=self.degiro_service,
        )

    def fixture_cash_movements_repository(self):
        data_file = pathlib.Path("tests/resources/stonks_overwatch/repositories/cash_movements_data.json")

        with open(data_file, "r") as file:
            data = json.load(file)

        for key, value in data.items():
            value["date"] = parse_datetime(value["date"])
            value["value_date"] = parse_datetime(value["value_date"])

            # Create and save the CashMovements object
            obj = DeGiroCashMovements.objects.create(**value)
            self.created_objects[key] = obj


    def fixture_product_info_repository(self):
        data_file = pathlib.Path("tests/resources/stonks_overwatch/repositories/product_info_data.json")

        with open(data_file, "r") as file:
            data = json.load(file)

        for key, value in data.items():
            # Create and save the ProductInfo object
            obj = DeGiroProductInfo.objects.create(**value)
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

    def test_get_dividends_from_account_overview(self):
        dividends = self.dividends_service.get_dividends()
        assert len(dividends) == 1

        assert dividends[0].date() == "2021-03-12"
        assert dividends[0].time() == "08:16:38"
        assert dividends[0].value_date() == "2021-03-11"
        assert dividends[0].value_time() == "23:59:59"
        assert dividends[0].stock_name == "Microsoft Corp"
        assert dividends[0].stock_symbol == "MSFT"
        assert dividends[0].description == "Dividend"
        assert dividends[0].type == "CASH_TRANSACTION"
        assert dividends[0].type_str() == "Cash Transaction"
        assert dividends[0].currency == "USD"
        assert dividends[0].change == 8.4
        assert dividends[0].formated_change() == "$ 8.40"

    def test_get_upcoming_dividends(self):
        with patch("requests_cache.CachedSession", requests.Session):
            with requests_mock.Mocker() as m:
                m.post(urls.LOGIN + "/totp", json={"sessionId": "abcdefg12345"}, status_code=200)
                m.get(
                    urls.CLIENT_DETAILS,
                    json={
                        "data": {
                            "clientRole": "basic",
                            "contractType": "PRIVATE",
                            "displayLanguage": "en",
                            "email": "user@domain.com",
                            "id": 98765,
                            "intAccount": 1234567,
                            "username": "someuser"
                        }
                    },
                    status_code=200,
                )
                m.register_uri(
                    "GET",
                    re.compile(re.escape(urls.UPCOMING_PAYMENTS) + r"/.*"),
                    json={
                        "data": [
                            {
                                "ca_id": "str",
                                "product": "Microsoft Corp",
                                "description": "Dividend 0.555 * 10.00 aandelen",
                                "currency": "USD",
                                "amount": "5.55",
                                "amountInBaseCurr": "7.79",
                                "payDate": "2024-10-03",
                            }
                        ]
                    },
                    status_code=200,
                )

                upcoming_dividends = self.dividends_service.get_upcoming_dividends()

                assert len(upcoming_dividends) == 1
