import pathlib
from unittest.mock import Mock, patch

import pytest

from degiro.config.degiro_config import DegiroConfig, DegiroCredentials
from degiro.services.degiro_service import CredentialsManager, DeGiroService


@pytest.fixture
def mock_degiro_config():
    with patch("degiro.config.degiro_config.DegiroConfig.default") as mock_config:
        file = pathlib.Path("tests/resources/degiro/config/sample-config.json")
        mock_config.return_value = DegiroConfig.from_json_file(file)
        yield mock_config

@pytest.fixture
def mock_credentials():
    return DegiroCredentials(
        username="testuser",
        password="testpassword",
        int_account=987654,
        totp_secret_key="ABCDEFGHIJKLMNOP",
        one_time_password=123456,
        user_token="token123"
    )

@pytest.fixture
def mock_degiro_client(mock_credentials):
    with patch("degiro.services.degiro_service.DeGiroService") as mock_degiro_client:
        mock_degiro_client.connect = Mock()
        mock_degiro_client.return_value  = DeGiroService(CredentialsManager(mock_credentials))
        yield mock_degiro_client

def test_credentials_manager_init(mock_degiro_config, mock_credentials):
        manager = CredentialsManager(mock_credentials)
        assert manager.credentials.username == mock_credentials.username
        assert manager.credentials.password == mock_credentials.password
        assert manager.credentials.int_account == mock_credentials.int_account
        assert manager.credentials.totp_secret_key == mock_credentials.totp_secret_key
        assert manager.credentials.one_time_password == mock_credentials.one_time_password
        # assert manager.credentials.user_token == mock_credentials.user_token

def test_degiro_service_init(mock_degiro_config, mock_credentials):
    manager = CredentialsManager(mock_credentials)
    service = DeGiroService(manager)
    assert service.credentials_manager == manager

def test_degiro_service_connect(mock_degiro_client):
    mock_degiro_client.connect()

