
import pathlib
from unittest.mock import patch

import requests

import pytest
from degiro.config.degiro_config import DegiroConfig, DegiroCredentials


@pytest.fixture
def mock_degiro_config():
    with patch("degiro.config.degiro_config.DegiroConfig.default") as mock_config:
        file = pathlib.Path("tests/resources/degiro/config/sample-config.json")
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
        user_token="token123"
    )

# Pytest Fixture to disable the usage of request-cache
@pytest.fixture(scope='function', autouse=True)
def disable_requests_cache():
    """Replace CachedSession with a regular Session for all test functions"""
    with patch('requests_cache.CachedSession', requests.Session):
        yield
