from datetime import datetime

from stonks_overwatch.repositories.degiro.models import DeGiroTransactions
from stonks_overwatch.repositories.degiro.transactions_repository import TransactionsRepository
from tests.stonks_overwatch.repositories.base_repository_test import BaseRepositoryTest

import pytest

@pytest.mark.django_db
class TestTransactionsRepository(BaseRepositoryTest):
    """Tests for the TransactionsRepository class.

    Test data includes:
    - Apple Inc (AAPL) transaction with ID 331868
    - Transaction details: Buy, 10 shares, total cost 2443.09
    """
    model_class = DeGiroTransactions
    data_file = "tests/resources/stonks_overwatch/repositories/degiro/transactions_data.json"

    def test_get_transactions_raw(self):
        """Test retrieving raw transaction data."""
        transactions = TransactionsRepository.get_transactions_raw()
        self.assert_list_length(transactions, 1)
        self.assert_dict_contains(
            transactions[0],
            productId=331868,
            buysell="B"
        )

    def test_get_products_transactions(self):
        """Test retrieving product transactions."""
        transactions = TransactionsRepository.get_products_transactions()
        self.assert_list_length(transactions, 1)
        self.assert_dict_contains(
            transactions[0],
            productId=331868,
            quantity=10
        )

    def test_get_product_transactions_not_found(self):
        """Test retrieving transactions for a non-existent product."""
        transactions = TransactionsRepository.get_product_transactions(['99999'])
        self.assert_list_length(transactions, 0)

    def test_get_product_transactions(self):
        """Test retrieving transactions for a specific product."""
        transactions = TransactionsRepository.get_product_transactions(['331868'])
        self.assert_list_length(transactions, 1)
        self.assert_dict_contains(
            transactions[0],
            productId=331868,
            quantity=10
        )

    def test_get_last_movement(self):
        """Test retrieving the last transaction movement."""
        last_movement = TransactionsRepository.get_last_movement()
        self.assertEqual(last_movement, datetime.fromisoformat("2020-03-11T18:01:46Z"))

    def test_get_portfolio_products(self):
        """Test retrieving portfolio products with their details."""
        portfolio_products = TransactionsRepository.get_portfolio_products()
        self.assert_list_length(portfolio_products, 1)
        self.assert_dict_contains(
            portfolio_products[0],
            productId=331868,
            size=10,
            totalPlusAllFeesInBaseCurrency=-2443.088933825,
            breakEvenPrice=244.3088933825
        )

    def test_get_last_movement_with_empty_db(self):
        """Test retrieving last movement when database is empty."""
        self.model_class.objects.all().delete()
        last_movement = TransactionsRepository.get_last_movement()
        self.assertIsNone(last_movement)
