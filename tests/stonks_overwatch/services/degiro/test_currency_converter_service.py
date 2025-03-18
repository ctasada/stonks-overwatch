import json
import pathlib

from stonks_overwatch.repositories.degiro.models import DeGiroProductQuotation
from stonks_overwatch.services.degiro.constants import CurrencyFX
from stonks_overwatch.services.degiro.currency_converter_service import CurrencyConverterService
from stonks_overwatch.utils.localization import LocalizationUtility

import pytest
from django.test import TestCase

@pytest.mark.django_db
class TestCurrencyConverterService(TestCase):
    def setUp(self):
        self.fixture_product_quotation_repository()
        self.currency_service = CurrencyConverterService()

    def fixture_product_quotation_repository(self):
        data_file = pathlib.Path("tests/resources/stonks_overwatch/repositories/product_quotations_data.json")

        with open(data_file, "r") as file:
            data = json.load(file)

        self.created_objects = {}
        for key, value in data.items():
            # Create and save the ProductQuotation object
            obj = DeGiroProductQuotation.objects.create(
                id=key,
                interval="P1D",
                last_import=LocalizationUtility.now(),
                quotations=value
            )
            self.created_objects[key] = obj

    def tearDown(self):
        # Clean up the created objects
        for obj in self.created_objects.values():
            obj.delete()

    def test_currency_fx_pairs(self):
        expected = ["EUR", "USD"]
        pairs = CurrencyFX.known_currencies()
        assert len(pairs) == 2
        assert all(a == b for a, b in zip(pairs, expected, strict=True))

    def test_calculate_maps(self):
        calculated_map = self.currency_service._CurrencyConverterService__calculate_maps()

        assert calculated_map == {
            'EUR': {
                'USD': {
                    'productId': CurrencyFX.EUR_USD.value,
                    'inverse': False
                }
            },
            'USD': {
                'EUR': {
                    'productId': CurrencyFX.EUR_USD.value,
                    'inverse': True
                }
            }
        }

        # If this fails, means we have missing maps
        mapped_keys = list(calculated_map.keys())
        mapped_keys.sort()
        assert CurrencyFX.known_currencies() == mapped_keys

    def test_convert_eur_to_eur(self):
        result = self.currency_service.convert(1.0, "EUR", "EUR")
        assert result == 1.0

    def test_convert_eur_to_usd_with_date(self):
        result = self.currency_service.convert(1.0, "EUR", "USD",
                                               LocalizationUtility.convert_string_to_date("2020-03-14"))
        assert round(result, 3) == round(1.1101, 3)

    def test_convert_usd_to_eur_with_date(self):
        result = self.currency_service.convert(1.0, "USD", "EUR",
                                               LocalizationUtility.convert_string_to_date("2020-03-14"))
        assert round(result, 3) == round(0.9008, 3)

    def test_convert_eur_to_usd(self):
        result = self.currency_service.convert(1.0, "EUR", "USD")
        assert round(result, 3) == round(1.116, 3)

    def test_convert_usd_to_eur(self):
        result = self.currency_service.convert(1.0, "USD", "EUR")
        assert round(result, 3) == round(0.896, 3)
