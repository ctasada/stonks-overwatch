import json
import pathlib

from django.test import TestCase

import pytest
from degiro.models import ProductInfo
from degiro.repositories.product_info_repository import ProductInfoRepository


@pytest.mark.django_db
class TestProductInfoRepository(TestCase):
    def setUp(self):
        self.repository = ProductInfoRepository()

        data_file = pathlib.Path("tests/resources/degiro/repositories/product_info_data.json")

        with open(data_file, "r") as file:
            data = json.load(file)

        self.created_objects = {}
        for key, value in data.items():
            # Create and save the ProductInfo object
            obj = ProductInfo.objects.create(**value)
            self.created_objects[key] = obj

    def tearDown(self):
        # Clean up the created objects
        for obj in self.created_objects.values():
            obj.delete()

    def test_get_products_info_raw(self):
        products = self.repository.get_products_info_raw(["332111", "331868"])

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
        product = self.repository.get_product_info_from_id(332111)

        assert product["name"] == "Microsoft Corp"
        assert product["symbol"] == "MSFT"
        assert product["currency"] == "USD"
        assert product["isin"] == "US5949181045"

        product = self.repository.get_product_info_from_id(331868)

        assert product["name"] == "Apple Inc"
        assert product["symbol"] == "AAPL"
        assert product["currency"] == "USD"
        assert product["isin"] == "US0378331005"

    def test_get_product_info_from_name(self):
        product = self.repository.get_product_info_from_name("Microsoft Corp")

        assert product["name"] == "Microsoft Corp"
        assert product["symbol"] == "MSFT"
        assert product["currency"] == "USD"
        assert product["isin"] == "US5949181045"

    def test_get_product_info_from_isin(self):
        products = self.repository.get_products_isin()

        print(products)
        assert sorted(products) == sorted(["US5949181045", "US0378331005"])
