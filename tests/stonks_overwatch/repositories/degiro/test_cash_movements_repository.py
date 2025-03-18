import json
import pathlib

from django.utils.dateparse import parse_datetime

from stonks_overwatch.repositories.degiro.cash_movements_repository import CashMovementsRepository
from stonks_overwatch.repositories.degiro.models import DeGiroCashMovements
from tests.stonks_overwatch.assertions import assert_dates_descending

import pytest
from django.test import TestCase

@pytest.mark.django_db
class TestCashMovementsRepository(TestCase):
    def setUp(self):
        self.fixture_cash_movements_repository()

    def fixture_cash_movements_repository(self):
        data_file = pathlib.Path("tests/resources/stonks_overwatch/repositories/cash_movements_data.json")

        with open(data_file, "r") as file:
            data = json.load(file)

        self.created_objects = {}
        for key, value in data.items():
            value["date"] = parse_datetime(value["date"])
            value["value_date"] = parse_datetime(value["value_date"])

            # Create and save the CashMovements object
            obj = DeGiroCashMovements.objects.create(**value)
            self.created_objects[key] = obj

    def tearDown(self):
        # Clean up the created objects
        for obj in self.created_objects.values():
            obj.delete()

    def test_get_cash_movements_raw(self):
        cash_movements = CashMovementsRepository.get_cash_movements_raw()
        assert len(cash_movements) == 8
        assert_dates_descending(cash_movements)

    def test_get_cash_deposits_raw(self):
        cash_deposits = CashMovementsRepository.get_cash_deposits_raw()
        assert len(cash_deposits) == 2
        assert cash_deposits[0]["description"] == "iDEAL storting"
        assert cash_deposits[1]["description"] == "iDEAL Deposit"

    def test_get_total_cash_deposits_raw(self):
        total_cash_deposits = CashMovementsRepository.get_total_cash_deposits_raw()
        assert total_cash_deposits == 300.0

    def test_get_total_cash(self):
        total_cash = CashMovementsRepository.get_total_cash()
        assert total_cash == 300.0

    def test_get_last_movement(self):
        last_movement = CashMovementsRepository.get_last_movement()
        assert last_movement == self.created_objects["flatex_cash_sweep"].date

    def test_get_last_movement_with_empty_db(self):
        DeGiroCashMovements.objects.all().delete()
        last_movement = CashMovementsRepository.get_last_movement()
        assert last_movement is None

    def test_get_cash_balance_by_date(self):
        cash_deposits = CashMovementsRepository.get_cash_balance_by_date()
        assert len(cash_deposits) == 2
        assert cash_deposits[0]["balanceTotal"] == '100.0'
        assert cash_deposits[1]["balanceTotal"] == '300.0'
