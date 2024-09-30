import json
import pathlib
from datetime import date

from django.test import TestCase

import pytest
from degiro.models import Transactions
from degiro.repositories.transactions_repository import TransactionsRepository


@pytest.mark.django_db
class TestTransactionsRepository(TestCase):
    def setUp(self):
        self.repository = TransactionsRepository()

        data_file = pathlib.Path("tests/resources/degiro/repositories/transactions_data.json")

        with open(data_file, "r") as file:
            data = json.load(file)

        self.created_objects = {}
        for key, value in data.items():
            # Create and save the Transactions object
            obj = Transactions.objects.create(**value)
            self.created_objects[key] = obj

    def tearDown(self):
        # Clean up the created objects
        for obj in self.created_objects.values():
            obj.delete()

    def test_get_transactions_raw(self):
        transactions = self.repository.get_transactions_raw()

        assert len(transactions) > 0
        assert transactions[0]["productId"] == 331868
        assert transactions[0]["buysell"] == "B"

    def test_get_last_movement(self):
        last_movement = self.repository.get_last_movement()

        assert last_movement == date.fromisoformat("2020-03-11")

    def test_get_last_movement_with_empty_db(self):
        Transactions.objects.all().delete()
        last_movement = self.repository.get_last_movement()
        assert last_movement is None
