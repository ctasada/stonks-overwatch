import json
import pathlib

from stonks_overwatch.services.brokers.degiro.repositories.models import DeGiroProductQuotation
from stonks_overwatch.services.brokers.degiro.repositories.product_quotations_repository import (
    ProductQuotationsRepository,
)
from stonks_overwatch.utils.core.localization import LocalizationUtility
from tests.stonks_overwatch.base_repository_test import BaseRepositoryTest

import pytest


@pytest.mark.django_db
class TestProductQuotationsRepository(BaseRepositoryTest):
    """Tests for the ProductQuotationsRepository class.

    Test data includes:
    - Microsoft Corp (MSFT) quotations
    - Daily prices: 50.85 (2020-03-11), 54.43 (2020-03-15)
    """

    model_class = DeGiroProductQuotation
    data_file = "tests/resources/stonks_overwatch/repositories/degiro/product_quotations_data.json"

    def load_test_data(self):
        """Override to handle additional fields for quotations."""
        data_file = pathlib.Path(self.data_file)

        with open(data_file, "r") as file:
            data = json.load(file)

        self.last_update = LocalizationUtility.now()
        self.created_objects = {}
        for key, value in data.items():
            obj = self.model_class.objects.create(
                id=key, interval="P1D", last_import=self.last_update, quotations=value
            )
            self.created_objects[key] = obj

    def test_get_product_quotations(self):
        """Test retrieving product quotations."""
        quotations = ProductQuotationsRepository.get_product_quotations(332111)
        self.assertIsNotNone(quotations)
        self.assertEqual(len(quotations), 5)
        self.assertEqual(quotations["2020-03-11"], 50.85)
        self.assertEqual(quotations["2020-03-15"], 54.43)

    def test_get_product_price(self):
        """Test retrieving the latest product price."""
        quotation = ProductQuotationsRepository.get_product_price(332111)
        self.assertAlmostEqual(quotation, 54.43, places=6)

    def test_get_product_price_when_not_found(self):
        """Test retrieving price for non-existent product."""
        quotation = ProductQuotationsRepository.get_product_price(123456)
        self.assertAlmostEqual(quotation, 0.0, places=6)

    def test_get_last_update(self):
        """Test retrieving the last update timestamp."""
        last_update = ProductQuotationsRepository.get_last_update()
        self.assertEqual(last_update, self.last_update)
