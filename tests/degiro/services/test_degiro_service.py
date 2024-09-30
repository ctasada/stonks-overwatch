import requests_mock
from degiro_connector.core.constants import urls
from degiro_connector.core.exceptions import DeGiroConnectionError

import pytest
from degiro.config.degiro_config import DegiroCredentials
from degiro.services.degiro_service import CredentialsManager, DeGiroService
from tests.degiro.fixtures import disable_requests_cache, mock_degiro_config, mock_full_credentials


def test_credentials_manager_init(mock_degiro_config: mock_degiro_config, mock_full_credentials: mock_full_credentials):
    manager = CredentialsManager(mock_full_credentials)
    assert manager.credentials.username == mock_full_credentials.username
    assert manager.credentials.password == mock_full_credentials.password
    assert manager.credentials.int_account == mock_full_credentials.int_account
    assert manager.credentials.totp_secret_key == mock_full_credentials.totp_secret_key
    assert manager.credentials.one_time_password == mock_full_credentials.one_time_password
    # assert manager.credentials.user_token == mock_credentials.user_token


def test_degiro_service_init(mock_degiro_config: mock_degiro_config, mock_full_credentials: mock_full_credentials):
    manager = CredentialsManager(mock_full_credentials)
    service = DeGiroService(manager)
    assert service.credentials_manager == manager


def test_degiro_service_connect_with_full_credential(
    disable_requests_cache: disable_requests_cache, mock_full_credentials: mock_full_credentials
):
    manager = CredentialsManager(mock_full_credentials)

    with requests_mock.Mocker() as m:
        m.post(urls.LOGIN + "/totp", json={"sessionId": "abcdefg12345"}, status_code=200)
        service = DeGiroService(manager)
        service.connect()

    assert service.check_connection() is True


def test_degiro_service_connect_with_credential(disable_requests_cache: disable_requests_cache):
    credential = DegiroCredentials(
        username="testuser",
        password="testpassword",
        totp_secret_key="ABCDEFGHIJKLMNOP",
    )
    manager = CredentialsManager(credential)

    with requests_mock.Mocker() as m:
        m.post(
            urls.LOGIN + "/totp",
            json={
                "isPassCodeEnabled": True,
                "locale": "nl_NL",
                "redirectUrl": "https://trader.degiro.nl/trader/",
                "sessionId": "abcdefg12345",
                "status": 0,
                "statusText": "success",
            },
            status_code=200,
        )
        service = DeGiroService(manager)

        # Check we have the right credentials
        assert service.api_client.credentials.username == credential.username
        assert service.api_client.credentials.password == credential.password
        assert service.api_client.credentials.totp_secret_key == credential.totp_secret_key
        assert service.api_client.credentials.one_time_password is None

        service.connect()

    assert service.check_connection() is True
    assert service.api_client.connection_storage.session_id == "abcdefg12345"


def test_degiro_service_connect_with_bad_credentials(disable_requests_cache: disable_requests_cache):
    credential = DegiroCredentials(username="testuser", password="testpassword")
    manager = CredentialsManager(credential)

    with requests_mock.Mocker() as m:
        m.post(urls.LOGIN, json={"loginFailures": 1, "status": 3, "statusText": "badCredentials"}, status_code=400)
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


def test_degiro_service_connect_with_missing_totp(disable_requests_cache: disable_requests_cache):
    credentials = DegiroCredentials(username="testuser", password="testpassword")
    manager = CredentialsManager(credentials)
    with requests_mock.Mocker() as m:
        m.post(urls.LOGIN, json={"status": 6, "statusText": "totpNeeded"}, status_code=202)
        service = DeGiroService(manager)

        # Check we have the right credentials
        assert service.api_client.credentials.username == credentials.username
        assert service.api_client.credentials.password == credentials.password
        assert service.api_client.credentials.totp_secret_key is None
        assert service.api_client.credentials.one_time_password is None

        with pytest.raises(DeGiroConnectionError) as exception_info:
            service.connect()

        assert exception_info.type is DeGiroConnectionError
        assert exception_info.value.error_details.status == 6


def test_degiro_service_update_credentials(disable_requests_cache: disable_requests_cache):
    credentials = DegiroCredentials(username="testuser", password="testpassword")
    manager = CredentialsManager(credentials)
    with requests_mock.Mocker() as m:
        m.post(urls.LOGIN, json={"status": 6, "statusText": "totpNeeded"}, status_code=202)
        service = DeGiroService(manager)

        # Check we have the right credentials
        assert service.api_client.credentials.username == credentials.username
        assert service.api_client.credentials.password == credentials.password
        assert service.api_client.credentials.totp_secret_key is None
        assert service.api_client.credentials.one_time_password is None

        with pytest.raises(DeGiroConnectionError) as exception_info:
            service.connect()

        assert exception_info.type is DeGiroConnectionError
        assert exception_info.value.error_details.status == 6

        credentials.one_time_password = 123456

        assert service.api_client.credentials.username == credentials.username
        assert service.api_client.credentials.password == credentials.password
        assert service.api_client.credentials.totp_secret_key is None
        assert service.api_client.credentials.one_time_password == 123456

        m.post(
            urls.LOGIN + "/totp",
            json={
                "isPassCodeEnabled": True,
                "locale": "nl_NL",
                "redirectUrl": "https://trader.degiro.nl/trader/",
                "sessionId": "abcdefg12345",
                "status": 0,
                "statusText": "success",
            },
            status_code=200,
        )

        service.connect()

        assert service.check_connection() is True
        assert service.api_client.connection_storage.session_id == "abcdefg12345"
