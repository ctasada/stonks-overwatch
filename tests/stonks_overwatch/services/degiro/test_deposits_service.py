import json
import pathlib

from isodate import parse_datetime

from stonks_overwatch.config.degiro_credentials import DegiroCredentials
from stonks_overwatch.services.brokers.degiro.client.degiro_client import CredentialsManager
from stonks_overwatch.services.brokers.degiro.repositories.models import DeGiroCashMovements
from stonks_overwatch.services.brokers.degiro.services.deposit_service import DepositsService
from stonks_overwatch.services.models import DepositType
from tests.stonks_overwatch.fixtures import DeGiroServiceTest

import pytest
from django.test import TestCase


@pytest.mark.django_db
class TestDepositsService(TestCase):
    def setUp(self):
        self.created_objects = {}
        self.fixture_cash_movements_repository()
        self.degiro_service = DeGiroServiceTest(CredentialsManager(self.fixture_credentials()))

        self.deposits_service = DepositsService(
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

    def test_get_cash_deposits(self):
        deposits = self.deposits_service.get_cash_deposits()

        assert len(deposits) == 3
        assert deposits[0].datetime_as_date() == "2024-09-15"
        assert deposits[0].currency == "EUR"
        assert deposits[0].change == -50.0
        assert deposits[0].description == "Terugstorting"
        assert deposits[0].type == DepositType.WITHDRAWAL

        assert deposits[1].datetime_as_date() == "2020-03-10"
        assert deposits[1].currency == "EUR"
        assert deposits[1].change == 100.0
        assert deposits[1].description == "iDEAL Storting"
        assert deposits[1].type == DepositType.DEPOSIT

    def test_calculate_cash_account_value(self):
        value = self.deposits_service.calculate_cash_account_value()

        assert value is not None
        assert value["2020-03-10"] == 300.0
        assert value["2024-09-15"] == 250.0
