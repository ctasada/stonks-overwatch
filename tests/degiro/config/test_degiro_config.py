import pathlib
from datetime import datetime

from degiro.config.degiro_config import DegiroConfig, DegiroCredentials


def test_degiro_credentials_init():
    username = "testuser"
    password = "testpassword"
    int_account = 123456
    totp_secret_key = "ABCDEFGHIJKLMNOP"
    one_time_password = 123456
    user_token = "token123"

    credentials = DegiroCredentials(
        username=username,
        password=password,
        int_account=int_account,
        totp_secret_key=totp_secret_key,
        one_time_password=one_time_password,
        user_token=user_token,
    )

    assert credentials.username == username
    assert credentials.password == password
    assert credentials.int_account == int_account
    assert credentials.totp_secret_key == totp_secret_key
    assert credentials.one_time_password == one_time_password
    assert credentials.user_token == user_token


def test_degiro_credentials_to_dict():
    credentials = DegiroCredentials(
        username="testuser",
        password="testpassword",
        int_account=123456,
        totp_secret_key="ABCDEFGHIJKLMNOP",
        one_time_password=123456,
        user_token="token123",
    )

    credentials_dict = credentials.to_dict()

    assert credentials_dict["username"] == "testuser"
    assert credentials_dict["password"] == "testpassword"
    assert credentials_dict["int_account"] == 123456
    assert credentials_dict["totp_secret_key"] == "ABCDEFGHIJKLMNOP"
    assert credentials_dict["one_time_password"] == 123456
    assert credentials_dict["user_token"] == "token123"


def test_degiro_credentials_from_dict():
    credentials_dict = {
        "username": "testuser",
        "password": "testpassword",
        "int_account": "123456",
        "totp_secret_key": "ABCDEFGHIJKLMNOP",
        "one_time_password": "123456",
        "user_token": "token123",
    }

    credentials = DegiroCredentials.from_dict(credentials_dict)

    assert credentials.username == "testuser"
    assert credentials.password == "testpassword"
    assert credentials.int_account == "123456"
    assert credentials.totp_secret_key == "ABCDEFGHIJKLMNOP"
    assert credentials.one_time_password == "123456"
    assert credentials.user_token == "token123"


def test_degiro_credentials_from_empty_dict():
    credentials_dict = {}

    credentials = DegiroCredentials.from_dict(credentials_dict)

    assert credentials.username == ""
    assert credentials.password == ""
    assert credentials.int_account is None
    assert credentials.totp_secret_key is None
    assert credentials.one_time_password is None
    assert credentials.user_token is None


def test_degiro_credentials_from_minimum_dict():
    credentials_dict = {"username": "testuser", "password": "testpassword"}

    credentials = DegiroCredentials.from_dict(credentials_dict)

    assert credentials.username == "testuser"
    assert credentials.password == "testpassword"
    assert credentials.int_account is None
    assert credentials.totp_secret_key is None
    assert credentials.one_time_password is None
    assert credentials.user_token is None


def test_degiro_config_init():
    username = "testuser"
    password = "testpassword"
    int_account = "123456"
    totp_secret_key = "ABCDEFGHIJKLMNOP"
    one_time_password = "123456"
    user_token = "token123"
    base_currency = "EUR"
    start_date = "2023-01-01"
    start_date_as_date = datetime.fromisoformat(start_date).date()

    credentials = DegiroCredentials(
        username=username,
        password=password,
        int_account=int_account,
        totp_secret_key=totp_secret_key,
        one_time_password=one_time_password,
        user_token=user_token,
    )

    config = DegiroConfig(credentials=credentials, base_currency=base_currency, start_date=start_date_as_date)

    assert config.credentials == credentials
    assert config.base_currency == base_currency
    assert config.start_date == start_date_as_date


def test_degiro_config_from_dict():
    credentials_dict = {
        "username": "testuser",
        "password": "testpassword",
        "int_account": 123456,
        "totp_secret_key": "ABCDEFGHIJKLMNOP",
        "one_time_password": 123456,
        "user_token": "token123",
    }
    base_currency = "EUR"
    start_date = "2023-01-01"
    start_date_as_date = datetime.fromisoformat(start_date).date()

    config_dict = {"credentials": credentials_dict, "base_currency": base_currency, "start_date": start_date}

    config = DegiroConfig.from_dict(config_dict)

    assert config.credentials == DegiroCredentials.from_dict(credentials_dict)
    assert config.base_currency == base_currency
    assert config.start_date == start_date_as_date


def test_degiro_config_from_json_file():
    credentials_dict = {
        "username": "testuser",
        "password": "testpassword",
        "int_account": 987654,
        "totp_secret_key": "ABCDEFGHIJKLMNOP",
        "one_time_password": 123456,
        "user_token": "token123",
    }
    base_currency = "EUR"
    start_date = "2023-01-01"
    start_date_as_date = datetime.fromisoformat(start_date).date()

    file = pathlib.Path("tests/resources/degiro/config/sample-config.json")
    config = DegiroConfig.from_json_file(file)

    assert config.credentials == DegiroCredentials.from_dict(credentials_dict)
    assert config.base_currency == base_currency
    assert config.start_date == start_date_as_date
