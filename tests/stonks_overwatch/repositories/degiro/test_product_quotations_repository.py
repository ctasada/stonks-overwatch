import json
import pathlib

from stonks_overwatch.repositories.degiro.models import DeGiroProductQuotation
from stonks_overwatch.repositories.degiro.product_quotations_repository import ProductQuotationsRepository
from stonks_overwatch.utils.localization import LocalizationUtility

import pytest
from django.test import TestCase

@pytest.mark.django_db
class TestProductQuotationsRepository(TestCase):
    def setUp(self):
        data_file = pathlib.Path("tests/resources/stonks_overwatch/repositories/product_quotations_data.json")

        with open(data_file, "r") as file:
            data = json.load(file)

        self.last_update = LocalizationUtility.now()
        self.created_objects = {}
        for key, value in data.items():
            # Create and save the ProductQuotation object
            obj = DeGiroProductQuotation.objects.create(
                id=key,
                interval="P1D",
                last_import=self.last_update,
                quotations=value
            )
            self.created_objects[key] = obj

    def tearDown(self):
        # Clean up the created objects
        for obj in self.created_objects.values():
            obj.delete()

    def test_get_product_quotations(self):
        quotations = ProductQuotationsRepository.get_product_quotations(332111)

        assert quotations is not None
        assert len(quotations) > 0
        assert quotations["2020-03-11"] == 50.85
        assert quotations["2020-03-15"] == 54.43

    def test_get_product_price(self):
        quotation = ProductQuotationsRepository.get_product_price(332111)

        assert quotation == 54.43

    def test_get_product_price_when_not_found(self):
        quotation = ProductQuotationsRepository.get_product_price(123456)

        assert quotation == 0.0

    def test_get_last_update(self):
        last_update = ProductQuotationsRepository.get_last_update()

        assert last_update == self.last_update
