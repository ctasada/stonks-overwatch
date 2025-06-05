import json
import pathlib

from django.utils.dateparse import parse_datetime

from stonks_overwatch.repositories.degiro.cash_movements_repository import CashMovementsRepository
from stonks_overwatch.repositories.degiro.models import DeGiroCashMovements
from tests.stonks_overwatch.assertions import assert_dates_descending
from tests.stonks_overwatch.repositories.base_repository_test import BaseRepositoryTest

import pytest

@pytest.mark.django_db
class TestCashMovementsRepository(BaseRepositoryTest):
    model_class = DeGiroCashMovements
    data_file = "tests/resources/stonks_overwatch/repositories/degiro/cash_movements_data.json"

    def load_test_data(self):
        """Override to handle date parsing for cash movements."""
        data_file = pathlib.Path(self.data_file)

        with open(data_file, "r") as file:
            data = json.load(file)

        self.created_objects = {}
        for key, value in data.items():
            value["date"] = parse_datetime(value["date"])
            value["value_date"] = parse_datetime(value["value_date"])
            obj = self.model_class.objects.create(**value)
            self.created_objects[key] = obj

    def test_get_cash_movements_raw(self):
        cash_movements = CashMovementsRepository.get_cash_movements_raw()
        assert len(cash_movements) == 9
        assert_dates_descending(cash_movements)

    def test_get_cash_deposits_raw(self):
        cash_deposits = CashMovementsRepository.get_cash_deposits_raw()
        assert len(cash_deposits) == 3
        assert cash_deposits[0]["description"] == "iDEAL storting"
        assert cash_deposits[1]["description"] == "iDEAL Deposit"
        assert cash_deposits[2]["description"] == "Terugstorting"

    def test_get_total_cash_deposits_raw(self):
        total_cash_deposits = CashMovementsRepository.get_total_cash_deposits_raw()
        assert total_cash_deposits == 250.0

    def test_get_total_cash(self):
        total_cash = CashMovementsRepository.get_total_cash('EUR')
        assert total_cash == 300.0

    def test_get_total_cash_from_nonexisting_currency(self):
        total_cash = CashMovementsRepository.get_total_cash('XXX')
        assert total_cash is None

    def test_get_last_movement(self):
        last_movement = CashMovementsRepository.get_last_movement()
        assert last_movement == self.get_test_object("flatex_cash_sweep").date

    def test_get_last_movement_with_empty_db(self):
        self.model_class.objects.all().delete()
        last_movement = CashMovementsRepository.get_last_movement()
        assert last_movement is None

    def test_get_cash_balance_by_date(self):
        cash_deposits = CashMovementsRepository.get_cash_balance_by_date()
        assert len(cash_deposits) == 3
        assert cash_deposits[0]["balanceTotal"] == '100.0'
        assert cash_deposits[1]["balanceTotal"] == '300.0'
        assert cash_deposits[2]["balanceTotal"] == '250.0'
