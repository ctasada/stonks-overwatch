from stonks_overwatch.services.brokers.degiro.repositories.models import DeGiroProductInfo
from stonks_overwatch.services.brokers.degiro.repositories.product_info_repository import ProductInfoRepository
from tests.stonks_overwatch.repositories.base_repository_test import BaseRepositoryTest

import pytest

@pytest.mark.django_db
class TestProductInfoRepository(BaseRepositoryTest):
    """Tests for the ProductInfoRepository class.

    Test data includes:
    - Microsoft Corp (MSFT) with ID 332111
    - Apple Inc (AAPL) with ID 331868
    """
    model_class = DeGiroProductInfo
    data_file = "tests/resources/stonks_overwatch/repositories/degiro/product_info_data.json"

    def test_get_products_info_raw(self):
        """Test retrieving raw product info for multiple products."""
        products = ProductInfoRepository.get_products_info_raw(["332111", "331868"])
        self.assert_list_length(products, 2)

        # Test Microsoft product info
        self.assert_dict_contains(
            products[332111],
            name="Microsoft Corp",
            symbol="MSFT",
            currency="USD",
            isin="US5949181045"
        )

        # Test Apple product info
        self.assert_dict_contains(
            products[331868],
            name="Apple Inc",
            symbol="AAPL",
            currency="USD",
            isin="US0378331005"
        )

    def test_get_product_by_id(self):
        """Test retrieving product info by ID."""
        # Test Microsoft product
        product = ProductInfoRepository.get_product_info_from_id(332111)
        self.assert_dict_contains(
            product,
            name="Microsoft Corp",
            symbol="MSFT",
            currency="USD",
            isin="US5949181045"
        )

        # Test Apple product
        product = ProductInfoRepository.get_product_info_from_id(331868)
        self.assert_dict_contains(
            product,
            name="Apple Inc",
            symbol="AAPL",
            currency="USD",
            isin="US0378331005"
        )

    def test_get_product_info_from_name(self):
        """Test retrieving product info by company name."""
        product = ProductInfoRepository.get_product_info_from_name("Microsoft Corp")
        self.assert_dict_contains(
            product,
            name="Microsoft Corp",
            symbol="MSFT",
            currency="USD",
            isin="US5949181045"
        )

    def test_get_product_info_from_isin(self):
        """Test retrieving product ISINs."""
        products = ProductInfoRepository.get_products_isin()
        self.assertEqual(sorted(products), sorted(["US5949181045", "US0378331005"]))

    def test_get_products_info_raw_by_symbol(self):
        """Test retrieving raw product info by stock symbols."""
        products = ProductInfoRepository.get_products_info_raw_by_symbol(["MSFT", "AAPL"])
        self.assert_list_length(products, 2)

        # Test Microsoft product info
        self.assert_dict_contains(
            products[332111],
            name="Microsoft Corp",
            symbol="MSFT",
            currency="USD",
            isin="US5949181045"
        )

        # Test Apple product info
        self.assert_dict_contains(
            products[331868],
            name="Apple Inc",
            symbol="AAPL",
            currency="USD",
            isin="US0378331005"
        )
