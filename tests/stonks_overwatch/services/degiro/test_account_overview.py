import json
import pathlib

from django.test import TestCase
from isodate import parse_datetime

import pytest
from stonks_overwatch.models import DeGiroCashMovements, DeGiroProductInfo
from stonks_overwatch.services.degiro.account_overview import AccountOverviewService


@pytest.mark.django_db
class TestAccountOverviewService(TestCase):
    def setUp(self):
        self.created_objects = {}
        self.fixture_cash_movements_repository()
        self.fixture_product_info_repository()

        self.account_overview = AccountOverviewService()

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

    def tearDown(self):
        # Clean up the created objects
        for obj in self.created_objects.values():
            obj.delete()

    def test_get_account_overview(self):
        overview = self.account_overview.get_account_overview()

        assert len(overview) == 8
        assert overview[0].date == "2024-09-16"
        assert overview[0].time == "18:46:52"
        assert overview[0].value_date == "2024-09-16"
        assert overview[0].value_time == "18:46:52"
        assert overview[0].stock_name == ""
        assert overview[0].stock_symbol == ""
        assert overview[0].description == "Degiro Cash Sweep Transfer"
        assert overview[0].type == "FLATEX_CASH_SWEEP"
        assert overview[0].type_str == "Flatex Cash Sweep"
        assert overview[0].currency == "EUR"
        assert overview[0].change == -14.36
        assert overview[0].formated_change == "€ -14.36"
        assert overview[0].total_balance == 0
        assert overview[0].formated_total_balance == ""
        assert overview[0].unsettled_cash == 0
        assert overview[0].formated_unsettled_cash == ""

        assert overview[1].date == "2024-08-29"
        assert overview[1].time == "14:33:41"
        assert overview[1].value_date == "2024-08-29"
        assert overview[1].value_time == "14:33:41"
        assert overview[1].stock_name == "Apple Inc"
        assert overview[1].stock_symbol == "AAPL"
        assert overview[1].description == "Koop 2 @ 100,000 EUR"
        assert overview[1].type == "TRANSACTION"
        assert overview[1].type_str == "Transaction"
        assert overview[1].currency == "EUR"
        assert overview[1].change == -200.0
        assert overview[1].formated_change == "€ -200.00"
        assert overview[1].total_balance == 0
        assert overview[1].formated_total_balance == ""
        assert overview[1].unsettled_cash == 0
        assert overview[1].formated_unsettled_cash == ""
