import pathlib
from unittest.mock import patch

import pytest
import requests
import requests_mock
from degiro_connector.core.constants import urls
from degiro_connector.core.exceptions import DeGiroConnectionError

from degiro.config.degiro_config import DegiroConfig, DegiroCredentials
from degiro.services.degiro_service import CredentialsManager, DeGiroService


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

def test_credentials_manager_init(mock_degiro_config, mock_full_credentials):
    manager = CredentialsManager(mock_full_credentials)
    assert manager.credentials.username == mock_full_credentials.username
    assert manager.credentials.password == mock_full_credentials.password
    assert manager.credentials.int_account == mock_full_credentials.int_account
    assert manager.credentials.totp_secret_key == mock_full_credentials.totp_secret_key
    assert manager.credentials.one_time_password == mock_full_credentials.one_time_password
    # assert manager.credentials.user_token == mock_credentials.user_token

def test_degiro_service_init(mock_degiro_config, mock_full_credentials):
    manager = CredentialsManager(mock_full_credentials)
    service = DeGiroService(manager)
    assert service.credentials_manager == manager

# Pytest Fixture to disable the usage of request-cache
@pytest.fixture(scope='function', autouse=True)
def disable_requests_cache():
    """Replace CachedSession with a regular Session for all test functions"""
    with patch('requests_cache.CachedSession', requests.Session):
        yield

def test_degiro_service_connect_with_full_credential(disable_requests_cache, mock_full_credentials):
    manager = CredentialsManager(mock_full_credentials)

    with requests_mock.Mocker() as m:
        m.post(urls.LOGIN + "/totp", json={'sessionId': 'abcdefg12345'}, status_code=200)
        service = DeGiroService(manager)
        service.connect()

    assert service.check_connection() is True

def test_degiro_service_connect_with_credential(disable_requests_cache):
    credential = DegiroCredentials(
            username="testuser",
            password="testpassword",
            totp_secret_key="ABCDEFGHIJKLMNOP",
    )
    manager = CredentialsManager(credential)

    with requests_mock.Mocker() as m:
        m.post(urls.LOGIN + "/totp", json={'sessionId': 'abcdefg12345'}, status_code=200)
        service = DeGiroService(manager)

        # Check we have the right credentials
        assert service.api_client.credentials.username == credential.username
        assert service.api_client.credentials.password == credential.password
        assert service.api_client.credentials.totp_secret_key == credential.totp_secret_key
        assert service.api_client.credentials.one_time_password is None

        service.connect()

    assert service.check_connection() is True
    assert service.api_client.connection_storage.session_id == 'abcdefg12345'

def test_degiro_service_connect_with_bad_credentials(disable_requests_cache):
    credential = DegiroCredentials(
            username="testuser",
            password="testpassword"
    )
    manager = CredentialsManager(credential)
    with requests_mock.Mocker() as m:
        m.post(urls.LOGIN, json={"loginFailures": 1,"status": 3,"statusText": "badCredentials"}, status_code=400)
        service = DeGiroService(manager)

        # Check we have the right credentials
        assert service.api_client.credentials.username == credential.username
        assert service.api_client.credentials.password == credential.password
        assert service.api_client.credentials.totp_secret_key is None
        assert service.api_client.credentials.one_time_password is None

        with pytest.raises(DeGiroConnectionError) as exception_info:
            service.connect()

        assert exception_info.type is DeGiroConnectionError
        assert exception_info.value.error_details.status == 3

def test_degiro_service_connect_with_missing_totp(disable_requests_cache):
    credential = DegiroCredentials(
            username="testuser",
            password="testpassword"
    )
    manager = CredentialsManager(credential)
    with requests_mock.Mocker() as m:
        m.post(urls.LOGIN, json={"loginFailures": 1,"status": 6,"statusText": "needs_otp"}, status_code=400)
        service = DeGiroService(manager)

        # Check we have the right credentials
        assert service.api_client.credentials.username == credential.username
        assert service.api_client.credentials.password == credential.password
        assert service.api_client.credentials.totp_secret_key is None
        assert service.api_client.credentials.one_time_password is None

        with pytest.raises(DeGiroConnectionError) as exception_info:
            service.connect()

        assert exception_info.type is DeGiroConnectionError
        assert exception_info.value.error_details.status == 6
