import json
import pathlib

from stonks_overwatch.services.brokers.degiro.repositories.company_profile_repository import CompanyProfileRepository
from stonks_overwatch.services.brokers.degiro.repositories.models import DeGiroCompanyProfile
from tests.stonks_overwatch.repositories.base_repository_test import BaseRepositoryTest

import pytest

@pytest.mark.django_db
class TestCompanyProfileRepository(BaseRepositoryTest):
    """Tests for the CompanyProfileRepository class.

    Test data includes:
    - Microsoft Corp (MSFT) with ISIN US5949181045
    - Company profile with 228,000 employees
    """
    model_class = DeGiroCompanyProfile
    data_file = "tests/resources/stonks_overwatch/repositories/degiro/company_profile_data.json"

    def load_test_data(self):
        """Override to handle ISIN as primary key."""
        data_file = pathlib.Path(self.data_file)

        with open(data_file, "r") as file:
            data = json.load(file)

        self.created_objects = {}
        for key, value in data.items():
            obj = self.model_class.objects.create(isin=key, data=value)
            self.created_objects[key] = obj

    def test_get_company_profile_raw(self):
        """Test retrieving raw company profile data."""
        # Test existing company profile
        company_profile = CompanyProfileRepository.get_company_profile_raw("US5949181045")
        self.assert_dict_contains(
            company_profile["data"],
            employees=228000
        )

        # Test non-existent company profile
        company_profile = CompanyProfileRepository.get_company_profile_raw("US04546C1062")
        assert company_profile == {}
