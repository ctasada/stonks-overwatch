import json
import pathlib

from django.test import TestCase

import pytest
from degiro.models import CompanyProfile
from degiro.repositories.company_profile_repository import CompanyProfileRepository


@pytest.mark.django_db
class TestCompanyProfileRepository(TestCase):
    def setUp(self):
        data_file = pathlib.Path("tests/resources/degiro/repositories/company_profile_data.json")

        with open(data_file, "r") as file:
            data = json.load(file)

        self.created_objects = {}
        for key, value in data.items():
            # Create and save the CompanyProfile object
            obj = CompanyProfile.objects.create(isin=key, data=value)
            self.created_objects[key] = obj

    def tearDown(self):
        # Clean up the created objects
        for obj in self.created_objects.values():
            obj.delete()

    def test_get_company_profile_raw(self):
        company_profile = CompanyProfileRepository.get_company_profile_raw("US5949181045")
        assert company_profile["data"]["employees"] == 228000

        company_profile = CompanyProfileRepository.get_company_profile_raw("US04546C1062")
        assert company_profile == {}
