import json
import pathlib
from datetime import date

from degiro_connector.core.constants import urls
from degiro_connector.core.exceptions import DeGiroConnectionError
from degiro_connector.quotecast.models.chart import Interval
from degiro_connector.trading.models.credentials import Credentials

from stonks_overwatch.services.degiro.degiro_service import CredentialsManager
from stonks_overwatch.utils.localization import LocalizationUtility
from tests.stonks_overwatch.fixtures import (
    TestDeGiroService,
    disable_requests_cache,
    mock_degiro_config,
    mock_full_credentials,
)

import pook
import pytest

def test_credentials_manager_init(mock_degiro_config: mock_degiro_config, mock_full_credentials: mock_full_credentials):
    manager = CredentialsManager(mock_full_credentials)
    assert manager.credentials.username == mock_full_credentials.username
    assert manager.credentials.password == mock_full_credentials.password
    assert manager.credentials.int_account == mock_full_credentials.int_account
    assert manager.credentials.totp_secret_key == mock_full_credentials.totp_secret_key
    assert manager.credentials.one_time_password == mock_full_credentials.one_time_password


def test_degiro_service_init(mock_degiro_config: mock_degiro_config, mock_full_credentials: mock_full_credentials):
    manager = CredentialsManager(mock_full_credentials)
    service = TestDeGiroService(manager)
    assert service.credentials_manager == manager


@pook.on
def test_degiro_service_connect_with_full_credential(
        disable_requests_cache: disable_requests_cache, mock_full_credentials: mock_full_credentials
):
    manager = CredentialsManager(mock_full_credentials)

    pook.post(urls.LOGIN + "/totp").reply(200).json({"sessionId": "abcdefg12345"})
    service = TestDeGiroService(manager)
    service.connect()

    assert service.check_connection() is True

@pook.on
def test_degiro_service_connect_with_credential(disable_requests_cache: disable_requests_cache):
    credential = Credentials(
        username="testuser",
        password="testpassword",
        totp_secret_key="ABCDEFGHIJKLMNOP",
    )
    manager = CredentialsManager(credential)

    pook.post(urls.LOGIN + "/totp").reply(200).json({
            "isPassCodeEnabled": True,
            "locale": "nl_NL",
            "redirectUrl": "https://trader.degiro.nl/trader/",
            "sessionId": "abcdefg12345",
            "status": 0,
            "statusText": "success",
        })
    pook.get(urls.CLIENT_DETAILS).reply(200).json({
            "data": {
                "clientRole": "basic",
                "contractType": "PRIVATE",
                "displayLanguage": "en",
                "email": "user@domain.com",
                "id": 98765,
                "intAccount": 1234567,
                "username": "someuser"
            }
        })
    service = TestDeGiroService(manager)

    # Check we have the right credentials
    assert service.api_client.credentials.username == credential.username
    assert service.api_client.credentials.password == credential.password
    assert service.api_client.credentials.totp_secret_key == credential.totp_secret_key
    assert service.api_client.credentials.one_time_password is None

    service.connect()

    assert service.check_connection() is True
    assert service.api_client.connection_storage.session_id == "abcdefg12345"


@pook.on
def test_degiro_service_connect_with_bad_credentials(disable_requests_cache: disable_requests_cache):
    credential = Credentials(username="testuser", password="testpassword")
    manager = CredentialsManager(credential)

    pook.post(urls.LOGIN).reply(400).json({"loginFailures": 1, "status": 3, "statusText": "badCredentials"})
    service = TestDeGiroService(manager)

    # Check we have the right credentials
    assert service.api_client.credentials.username == credential.username
    assert service.api_client.credentials.password == credential.password
    assert service.api_client.credentials.totp_secret_key is None
    assert service.api_client.credentials.one_time_password is None

    with pytest.raises(DeGiroConnectionError) as exception_info:
        service.connect()

    assert exception_info.type is DeGiroConnectionError
    assert exception_info.value.error_details.status == 3


@pook.on
def test_degiro_service_connect_with_missing_totp(disable_requests_cache: disable_requests_cache):
    credentials = Credentials(username="testuser", password="testpassword")
    manager = CredentialsManager(credentials)
    pook.post(urls.LOGIN).reply(202).json({"status": 6, "statusText": "totpNeeded"})
    service = TestDeGiroService(manager)

    # Check we have the right credentials
    assert service.api_client.credentials.username == credentials.username
    assert service.api_client.credentials.password == credentials.password
    assert service.api_client.credentials.totp_secret_key is None
    assert service.api_client.credentials.one_time_password is None

    with pytest.raises(DeGiroConnectionError) as exception_info:
        service.connect()

    assert exception_info.type is DeGiroConnectionError
    assert exception_info.value.error_details.status == 6


@pook.on
def test_degiro_service_update_credentials(disable_requests_cache: disable_requests_cache):
    credentials = Credentials(username="testuser", password="testpassword")
    manager = CredentialsManager(credentials)
    pook.post(urls.LOGIN).reply(202).json({"status": 6, "statusText": "totpNeeded"})
    service = TestDeGiroService(manager)

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

    pook.post(urls.LOGIN + "/totp").reply(200).json({
            "isPassCodeEnabled": True,
            "locale": "nl_NL",
            "redirectUrl": "https://trader.degiro.nl/trader/",
            "sessionId": "abcdefg12345",
            "status": 0,
            "statusText": "success",
        })

    service.connect()

    assert service.check_connection() is True
    assert service.api_client.connection_storage.session_id == "abcdefg12345"

@pook.on
def test_get_product_quotation(
        disable_requests_cache: disable_requests_cache,
        mock_full_credentials: mock_full_credentials
):
    manager = CredentialsManager(mock_full_credentials)
    chart_data_file = pathlib.Path("tests/resources/stonks_overwatch/services/aapl-chart-fetcher.json")
    with open(chart_data_file, "r") as file:
        chart_data = f"vwd.hchart.seriesRequestManager.sync_response({file.read()})"

    client_details_file = pathlib.Path("tests/resources/stonks_overwatch/services/client-details.json")
    with open(client_details_file, "r") as file:
        client_details = json.load(file)

    pook.post(urls.LOGIN + "/totp").reply(200).json({"sessionId": "abcdefg12345"})
    pook.get(urls.CLIENT_DETAILS + "?sessionId=abcdefg12345").reply(200).json(client_details)
    pook.get(urls.CHART).reply(200).json(chart_data)
    pook.get(urls.CHART).reply(200).json(chart_data)

    service = TestDeGiroService(manager)
    service.connect()

    quotes = service.get_product_quotation("350015372", "US0378331005", Interval.P1M, "AAPL")

    today = LocalizationUtility.format_date_from_date(date.today())

    assert service.check_connection() is True
    assert len(quotes.keys()) == 31
    assert quotes["2024-09-05"] == 222.38
    assert quotes["2024-09-06"] == 220.80
    assert quotes["2024-09-07"] == 220.80
    assert quotes["2024-09-08"] == 220.80
    assert quotes["2024-09-09"] == 220.91
    assert quotes["2024-10-04"] == 226.8
    assert quotes[today] == 226.8
