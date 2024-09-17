import json
import pathlib

from django.test import TestCase
from django.utils.dateparse import parse_datetime

import pytest
from degiro.models import CashMovements
from degiro.repositories.cash_movements_repository import CashMovementsRepository
from tests.degiro.assertions import assert_dates_descending


@pytest.mark.django_db
class TestCashMovementsRepository(TestCase):
    def setUp(self):
        # Known Cash Movement Types:
        # CASH_FUND_NAV_CHANGE
        # CASH_FUND_TRANSACTION
        # CASH_TRANSACTION
        # FLATEX_CASH_SWEEP
        # PAYMENT
        # TRANSACTION
        self.repository = CashMovementsRepository()
        data_file = pathlib.Path("tests/resources/degiro/repositories/cash_movements_data.json")

        with open(data_file, 'r') as file:
            data = json.load(file)

        self.created_objects = {}
        for key, value in data.items():
            value['date'] = parse_datetime(value['date'])
            value['value_date'] = parse_datetime(value['value_date'])

            # Create and save the CashMovements object
            obj = CashMovements.objects.create(**value)
            self.created_objects[key] = obj

    def tearDown(self):
        # Clean up the created objects
        for obj in self.created_objects.values():
            obj.delete()

    def test_get_cash_movements_raw(self):
        cash_movements = self.repository.get_cash_movements_raw()
        assert len(cash_movements) == 7
        assert_dates_descending(cash_movements)

    def test_get_cash_deposits_raw(self):
        cash_deposits = self.repository.get_cash_deposits_raw()
        assert len(cash_deposits) == 2
        assert cash_deposits[0]['description'] == 'iDEAL storting'
        assert cash_deposits[1]['description'] == 'iDEAL Deposit'

    def test_get_total_cash_deposits_raw(self):
        total_cash_deposits = self.repository.get_total_cash_deposits_raw()
        assert total_cash_deposits == 300.0

    def test_get_total_cash(self):
        total_cash = self.repository.get_total_cash()
        assert total_cash == 300.0

    def test_get_last_movement(self):
        last_movement = self.repository.get_last_movement()
        assert last_movement == self.created_objects['flatex_cash_sweep'].date.date()

    def test_get_last_movement_with_empty_db(self):
        CashMovements.objects.all().delete()
        last_movement = self.repository.get_last_movement()
        assert last_movement is None
