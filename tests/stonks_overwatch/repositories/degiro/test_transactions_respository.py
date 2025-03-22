import json
import pathlib
from datetime import datetime

from stonks_overwatch.repositories.degiro.models import DeGiroTransactions
from stonks_overwatch.repositories.degiro.transactions_repository import TransactionsRepository

import pytest
from django.test import TestCase

@pytest.mark.django_db
class TestTransactionsRepository(TestCase):
    def setUp(self):
        data_file = pathlib.Path("tests/resources/stonks_overwatch/repositories/degiro/transactions_data.json")

        with open(data_file, "r") as file:
            data = json.load(file)

        self.created_objects = {}
        for key, value in data.items():
            # Create and save the Transactions object
            obj = DeGiroTransactions.objects.create(**value)
            self.created_objects[key] = obj

    def tearDown(self):
        # Clean up the created objects
        for obj in self.created_objects.values():
            obj.delete()

    def test_get_transactions_raw(self):
        transactions = TransactionsRepository.get_transactions_raw()

        assert len(transactions) > 0
        assert transactions[0]["productId"] == 331868
        assert transactions[0]["buysell"] == "B"

    def test_get_products_transactions(self):
        transactions = TransactionsRepository.get_products_transactions()

        assert len(transactions) > 0
        assert transactions[0]["productId"] == 331868
        assert transactions[0]["quantity"] == 10

    def test_get_product_transactions_not_found(self):
        transactions = TransactionsRepository.get_product_transactions(['99999'])

        assert len(transactions) == 0

    def test_get_product_transactions(self):
        transactions = TransactionsRepository.get_product_transactions(['331868'])

        assert len(transactions) == 1
        assert transactions[0]["productId"] == 331868
        assert transactions[0]["quantity"] == 10


    def test_get_last_movement(self):
        last_movement = TransactionsRepository.get_last_movement()

        assert last_movement == datetime.fromisoformat("2020-03-11T18:01:46Z")

    def test_get_portfolio_products(self):
        portfolio_products = TransactionsRepository.get_portfolio_products()

        assert len(portfolio_products) > 0
        assert portfolio_products[0]["productId"] == 331868
        assert portfolio_products[0]["size"] == 10
        assert portfolio_products[0]["totalPlusAllFeesInBaseCurrency"] == -2443.088933825
        assert portfolio_products[0]["breakEvenPrice"] == 244.3088933825

    def test_get_last_movement_with_empty_db(self):
        DeGiroTransactions.objects.all().delete()
        last_movement = TransactionsRepository.get_last_movement()
        assert last_movement is None
