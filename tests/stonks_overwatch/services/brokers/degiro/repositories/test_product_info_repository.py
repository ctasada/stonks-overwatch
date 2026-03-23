from stonks_overwatch.services.brokers.degiro.repositories.models import DeGiroProductInfo
from stonks_overwatch.services.brokers.degiro.repositories.product_info_repository import ProductInfoRepository
from tests.stonks_overwatch.base_repository_test import BaseRepositoryTest

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
            products[332111], name="Microsoft Corp", symbol="MSFT", currency="USD", isin="US5949181045"
        )

        # Test Apple product info
        self.assert_dict_contains(
            products[331868], name="Apple Inc", symbol="AAPL", currency="USD", isin="US0378331005"
        )

    def test_get_product_by_id(self):
        """Test retrieving product info by ID."""
        # Test Microsoft product
        product = ProductInfoRepository.get_product_info_from_id(332111)
        self.assert_dict_contains(product, name="Microsoft Corp", symbol="MSFT", currency="USD", isin="US5949181045")

        # Test Apple product
        product = ProductInfoRepository.get_product_info_from_id(331868)
        self.assert_dict_contains(product, name="Apple Inc", symbol="AAPL", currency="USD", isin="US0378331005")

    def test_get_product_by_id_not_found_returns_empty_dict(self):
        """Test that a missing product ID returns an empty dict instead of raising KeyError."""
        product = ProductInfoRepository.get_product_info_from_id(999999)
        self.assertEqual(product, {})

    def test_get_product_info_from_name(self):
        """Test retrieving product info by company name."""
        product = ProductInfoRepository.get_product_info_from_name("Microsoft Corp")
        self.assert_dict_contains(product, name="Microsoft Corp", symbol="MSFT", currency="USD", isin="US5949181045")

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
            products[332111], name="Microsoft Corp", symbol="MSFT", currency="USD", isin="US5949181045"
        )

        # Test Apple product info
        self.assert_dict_contains(
            products[331868], name="Apple Inc", symbol="AAPL", currency="USD", isin="US0378331005"
        )

    # --- WARRANT / LEVERAGED products (no symbol in DeGiro API response) ---

    WARRANT_PRODUCT = {
        "id": 18960776,
        "name": "MiniS O.End DAX 17230",
        "isin": "DE000VP4KR02",
        "symbol": "",  # DeGiro API omits 'symbol' for these product types; stored as ""
        "contract_size": 1.0,
        "product_type": "WARRANT",
        "product_type_id": 536,
        "tradable": False,
        "category": "D",
        "currency": "EUR",
        "active": False,
        "exchange_id": "195",
        "only_eod_prices": False,
    }

    def test_warrant_product_stored_with_empty_symbol_is_retrievable_by_id(self):
        """A WARRANT product stored with symbol='' must be found by ID without raising KeyError.
        Previously __import_products_info crashed on row["symbol"], so these products were never
        stored, and get_product_info_from_id raised KeyError: <product_id>."""
        DeGiroProductInfo.objects.create(**self.WARRANT_PRODUCT)

        product = ProductInfoRepository.get_product_info_from_id(18960776)

        self.assert_dict_contains(product, name="MiniS O.End DAX 17230", symbol="", currency="EUR")

    def test_get_products_info_raw_by_empty_symbol_does_not_return_normal_stocks(self):
        """Querying by symbol='' must only return products that have an empty symbol.
        This guards _get_correlated_products: if it queried '' it would return all
        WARRANT products as 'correlated', corrupting realized P&L calculations."""
        DeGiroProductInfo.objects.create(**self.WARRANT_PRODUCT)

        products = ProductInfoRepository.get_products_info_raw_by_symbol([""])

        # Only the WARRANT with empty symbol should be returned — not MSFT or AAPL
        self.assert_list_length(products, 1)
        self.assertIn(18960776, products)
        self.assertNotIn(332111, products)
        self.assertNotIn(331868, products)
