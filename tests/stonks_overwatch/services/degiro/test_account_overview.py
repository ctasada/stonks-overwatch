import json
import pathlib

from isodate import parse_datetime

from stonks_overwatch.services.brokers.degiro.repositories.models import DeGiroCashMovements, DeGiroProductInfo
from stonks_overwatch.services.brokers.degiro.services.account_service import AccountOverviewService

import pytest
from django.test import TestCase

@pytest.mark.django_db
class TestAccountOverviewService(TestCase):
    def setUp(self):
        self.created_objects = {}
        self.fixture_cash_movements_repository()
        self.fixture_product_info_repository()

        self.account_overview = AccountOverviewService()

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

    def tearDown(self):
        # Clean up the created objects
        for obj in self.created_objects.values():
            obj.delete()

    def test_get_account_overview(self):
        overview = self.account_overview.get_account_overview()

        assert len(overview) == 9
        assert overview[0].date() == "2024-09-16"
        assert overview[0].time() == "18:46:52"
        assert overview[0].value_date() == "2024-09-16"
        assert overview[0].value_time() == "18:46:52"
        assert overview[0].stock_name == ""
        assert overview[0].stock_symbol == ""
        assert overview[0].description == "Degiro Cash Sweep Transfer"
        assert overview[0].type == "FLATEX_CASH_SWEEP"
        assert overview[0].type_str() == "Flatex Cash Sweep"
        assert overview[0].currency == "EUR"
        assert overview[0].change == -14.36
        assert overview[0].formated_change() == "€ -14.36"

        assert overview[2].date() == "2024-08-29"
        assert overview[2].time() == "14:33:41"
        assert overview[2].value_date() == "2024-08-29"
        assert overview[2].value_time() == "14:33:41"
        assert overview[2].stock_name == "Apple Inc"
        assert overview[2].stock_symbol == "AAPL"
        assert overview[2].description == "Koop 2 @ 100,000 EUR"
        assert overview[2].type == "TRANSACTION"
        assert overview[2].type_str() == "Transaction"
        assert overview[2].currency == "EUR"
        assert overview[2].change == -200.0
        assert overview[2].formated_change() == "€ -200.00"
