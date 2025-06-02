import json
import pathlib

from django.utils.dateparse import parse_datetime

from stonks_overwatch.repositories.degiro.dividends_repository import DividendsRepository
from stonks_overwatch.repositories.degiro.models import DeGiroUpcomingPayments
from tests.stonks_overwatch.assertions import assert_dates_descending
from tests.stonks_overwatch.repositories.base_repository_test import BaseRepositoryTest

import pytest

@pytest.mark.django_db
class TestDividendsRepository(BaseRepositoryTest):
    model_class = DeGiroUpcomingPayments
    data_file = "tests/resources/stonks_overwatch/repositories/degiro/dividends_upcoming_data.json"

    def load_test_data(self):
        """Override to handle date parsing for cash movements."""
        data_file = pathlib.Path(self.data_file)

        with open(data_file, "r") as file:
            data = json.load(file)

        self.created_objects = {}
        for key, value in data.items():
            value["pay_date"]= parse_datetime(value["pay_date"])
            obj = self.model_class.objects.create(**value)
            self.created_objects[key] = obj

    def test_get_cash_movements_raw(self):
        upcoming_dividends = DividendsRepository.get_upcoming_payments()
        assert len(upcoming_dividends) == 6
        assert_dates_descending(data=upcoming_dividends, date_column="payDate")
