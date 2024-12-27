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
        assert overview[0]["date"] == "2024-09-16"
        assert overview[0]["time"] == "18:46:52"
        assert overview[0]["valueDate"] == "2024-09-16"
        assert overview[0]["valueTime"] == "18:46:52"
        assert overview[0]["stockName"] == ""
        assert overview[0]["stockSymbol"] == ""
        assert overview[0]["description"] == "Degiro Cash Sweep Transfer"
        assert overview[0]["type"] == "FLATEX_CASH_SWEEP"
        assert overview[0]["typeStr"] == "Flatex Cash Sweep"
        assert overview[0]["currency"] == "EUR"
        assert overview[0]["change"] == -14.36
        assert overview[0]["formatedChange"] == "€ -14.36"
        assert overview[0]["totalBalance"] == 0
        assert overview[0]["formatedTotalBalance"] == ""
        assert overview[0]["unsettledCash"] == 0
        assert overview[0]["formatedUnsettledCash"] == ""

        assert overview[1]["date"] == "2024-08-29"
        assert overview[1]["time"] == "14:33:41"
        assert overview[1]["valueDate"] == "2024-08-29"
        assert overview[1]["valueTime"] == "14:33:41"
        assert overview[1]["stockName"] == "Apple Inc"
        assert overview[1]["stockSymbol"] == "AAPL"
        assert overview[1]["description"] == "Koop 2 @ 100,000 EUR"
        assert overview[1]["type"] == "TRANSACTION"
        assert overview[1]["typeStr"] == "Transaction"
        assert overview[1]["currency"] == "EUR"
        assert overview[1]["change"] == -200.0
        assert overview[1]["formatedChange"] == "€ -200.00"
        assert overview[1]["totalBalance"] == 0
        assert overview[1]["formatedTotalBalance"] == ""
        assert overview[1]["unsettledCash"] == 0
        assert overview[1]["formatedUnsettledCash"] == ""
