import json
import pathlib

from django.test import TestCase

import pytest
from stonks_overwatch.repositories.degiro.models import DeGiroProductInfo
from stonks_overwatch.repositories.degiro.product_info_repository import ProductInfoRepository

import pytest
from django.test import TestCase

@pytest.mark.django_db
class TestProductInfoRepository(TestCase):
    def setUp(self):
        data_file = pathlib.Path("tests/resources/stonks_overwatch/repositories/product_info_data.json")

        with open(data_file, "r") as file:
            data = json.load(file)

        self.created_objects = {}
        for key, value in data.items():
            # Create and save the ProductInfo object
            obj = DeGiroProductInfo.objects.create(**value)
            self.created_objects[key] = obj

    def tearDown(self):
        # Clean up the created objects
        for obj in self.created_objects.values():
            obj.delete()

    def test_get_products_info_raw(self):
        products = ProductInfoRepository.get_products_info_raw(["332111", "331868"])

        assert len(products) > 0

        assert products[332111]["name"] == "Microsoft Corp"
        assert products[332111]["symbol"] == "MSFT"
        assert products[332111]["currency"] == "USD"
        assert products[332111]["isin"] == "US5949181045"

        assert products[331868]["name"] == "Apple Inc"
        assert products[331868]["symbol"] == "AAPL"
        assert products[331868]["currency"] == "USD"
        assert products[331868]["isin"] == "US0378331005"

    def test_get_product_by_id(self):
        product = ProductInfoRepository.get_product_info_from_id(332111)

        assert product["name"] == "Microsoft Corp"
        assert product["symbol"] == "MSFT"
        assert product["currency"] == "USD"
        assert product["isin"] == "US5949181045"

        product = ProductInfoRepository.get_product_info_from_id(331868)

        assert product["name"] == "Apple Inc"
        assert product["symbol"] == "AAPL"
        assert product["currency"] == "USD"
        assert product["isin"] == "US0378331005"

    def test_get_product_info_from_name(self):
        product = ProductInfoRepository.get_product_info_from_name("Microsoft Corp")

        assert product["name"] == "Microsoft Corp"
        assert product["symbol"] == "MSFT"
        assert product["currency"] == "USD"
        assert product["isin"] == "US5949181045"

    def test_get_product_info_from_isin(self):
        products = ProductInfoRepository.get_products_isin()

        print(products)
        assert sorted(products) == sorted(["US5949181045", "US0378331005"])

    def test_get_products_info_raw_by_symbol(self):
        products = ProductInfoRepository.get_products_info_raw_by_symbol(["MSFT", "AAPL"])

        assert len(products) == 2

        assert products[332111]["name"] == "Microsoft Corp"
        assert products[332111]["symbol"] == "MSFT"
        assert products[332111]["currency"] == "USD"
        assert products[332111]["isin"] == "US5949181045"

        assert products[331868]["name"] == "Apple Inc"
        assert products[331868]["symbol"] == "AAPL"
        assert products[331868]["currency"] == "USD"
        assert products[331868]["isin"] == "US0378331005"
