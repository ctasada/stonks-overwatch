import pathlib

import requests

from stonks_overwatch.config.degiro import DegiroConfig, DegiroCredentials
from stonks_overwatch.services.brokers.degiro.client.degiro_client import DeGiroService

import pytest
from unittest.mock import patch


@pytest.fixture
def mock_degiro_config():
    with patch("stonks_overwatch.config.degiro.DegiroConfig.default") as mock_config:
        file = pathlib.Path("tests/resources/stonks_overwatch/config/sample-config.json")
        mock_config.return_value = DegiroConfig.from_json_file(file)
        yield mock_config


@pytest.fixture
def mock_full_credentials():
    return DegiroCredentials(
        username="testuser",
        password="testpassword",
        int_account=987654,
        totp_secret_key="ABCDEFGHIJKLMNOP",
        one_time_password=123456,
    )


# Pytest Fixture to disable the usage of request-cache
@pytest.fixture(scope="function", autouse=True)
def disable_requests_cache():
    """Replace CachedSession with a regular Session for all test functions"""
    with patch("requests_cache.CachedSession", requests.Session):
        yield


class DeGiroServiceTest(DeGiroService):
    """Test specific DeGiroService to avoid the singleton limitations"""

    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)
