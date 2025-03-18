import pathlib
from datetime import datetime

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.config import Config
from stonks_overwatch.config.degiro_config import DegiroConfig
from stonks_overwatch.config.degiro_credentials import DegiroCredentials

def test_degiro_credentials_init():
    username = "testuser"
    password = "testpassword"
    int_account = 123456
    totp_secret_key = "ABCDEFGHIJKLMNOP"
    one_time_password = 123456

    credentials = DegiroCredentials(
        username=username,
        password=password,
        int_account=int_account,
        totp_secret_key=totp_secret_key,
        one_time_password=one_time_password,
    )

    assert credentials.username == username
    assert credentials.password == password
    assert credentials.int_account == int_account
    assert credentials.totp_secret_key == totp_secret_key
    assert credentials.one_time_password == one_time_password


def test_degiro_credentials_to_dict():
    credentials = DegiroCredentials(
        username="testuser",
        password="testpassword",
        int_account=123456,
        totp_secret_key="ABCDEFGHIJKLMNOP",
        one_time_password=123456,
    )

    credentials_dict = credentials.to_dict()

    assert credentials_dict["username"] == "testuser"
    assert credentials_dict["password"] == "testpassword"
    assert credentials_dict["int_account"] == 123456
    assert credentials_dict["totp_secret_key"] == "ABCDEFGHIJKLMNOP"
    assert credentials_dict["one_time_password"] == 123456


def test_degiro_credentials_from_dict():
    credentials_dict = {
        "username": "testuser",
        "password": "testpassword",
        "int_account": "123456",
        "totp_secret_key": "ABCDEFGHIJKLMNOP",
        "one_time_password": "123456",
    }

    credentials = DegiroCredentials.from_dict(credentials_dict)

    assert credentials.username == "testuser"
    assert credentials.password == "testpassword"
    assert credentials.int_account == "123456"
    assert credentials.totp_secret_key == "ABCDEFGHIJKLMNOP"
    assert credentials.one_time_password == "123456"


def test_degiro_credentials_from_empty_dict():
    credentials_dict = {}

    credentials = DegiroCredentials.from_dict(credentials_dict)

    assert credentials.username == ""
    assert credentials.password == ""
    assert credentials.int_account is None
    assert credentials.totp_secret_key is None
    assert credentials.one_time_password is None


def test_degiro_credentials_from_minimum_dict():
    credentials_dict = {"username": "testuser", "password": "testpassword"}

    credentials = DegiroCredentials.from_dict(credentials_dict)

    assert credentials.username == "testuser"
    assert credentials.password == "testpassword"
    assert credentials.int_account is None
    assert credentials.totp_secret_key is None
    assert credentials.one_time_password is None


def test_config_init():
    base_currency = "EUR"

    username = "testuser"
    password = "testpassword"
    int_account = "123456"
    totp_secret_key = "ABCDEFGHIJKLMNOP"
    one_time_password = "123456"
    start_date = "2023-01-01"
    start_date_as_date = datetime.fromisoformat(start_date).date()

    credentials = DegiroCredentials(
        username=username,
        password=password,
        int_account=int_account,
        totp_secret_key=totp_secret_key,
        one_time_password=one_time_password,
    )

    degiro_config = DegiroConfig(credentials=credentials, start_date=start_date_as_date)
    config = Config(base_currency=base_currency, degiro_configuration=degiro_config)

    assert config.base_currency == base_currency
    assert config.degiro_configuration.credentials == credentials
    assert config.degiro_configuration.start_date == start_date_as_date


def test_config_from_dict():
    base_currency = "EUR"
    credentials_dict = {
        "username": "testuser",
        "password": "testpassword",
        "int_account": 123456,
        "totp_secret_key": "ABCDEFGHIJKLMNOP",
        "one_time_password": 123456,
    }
    start_date = "2023-01-01"
    start_date_as_date = datetime.fromisoformat(start_date).date()

    config_dict = {
        "base_currency": base_currency,
        "degiro": {
            "credentials": credentials_dict,
            "start_date": start_date
        }
    }

    config = Config.from_dict(config_dict)

    assert config.base_currency == base_currency
    assert config.degiro_configuration.credentials == DegiroCredentials.from_dict(credentials_dict)
    assert config.degiro_configuration.start_date == start_date_as_date


def test_config_from_json_file():
    base_currency = "EUR"
    credentials_dict = {
        "username": "testuser",
        "password": "testpassword",
        "int_account": 987654,
        "totp_secret_key": "ABCDEFGHIJKLMNOP",
        "one_time_password": 123456,
    }
    start_date = "2023-01-01"
    start_date_as_date = datetime.fromisoformat(start_date).date()
    update_frequency_minutes = 5

    file = pathlib.Path("tests/resources/stonks_overwatch/config/sample-config.json")
    config = Config.from_json_file(file)

    assert config.base_currency == base_currency
    assert config.degiro_configuration.credentials == DegiroCredentials.from_dict(credentials_dict)
    assert config.degiro_configuration.start_date == start_date_as_date
    assert config.degiro_configuration.update_frequency_minutes == update_frequency_minutes

def test_config_default():
    BaseConfig.CONFIG_PATH = "tests/resources/stonks_overwatch/config/sample-config.json"
    base_currency = "EUR"
    credentials_dict = {
        "username": "testuser",
        "password": "testpassword",
        "int_account": 987654,
        "totp_secret_key": "ABCDEFGHIJKLMNOP",
        "one_time_password": 123456,
    }
    start_date = "2023-01-01"
    start_date_as_date = datetime.fromisoformat(start_date).date()
    update_frequency_minutes = 5

    config = Config.default()

    assert config.base_currency == base_currency
    assert config.degiro_configuration.credentials == DegiroCredentials.from_dict(credentials_dict)
    assert config.degiro_configuration.start_date == start_date_as_date
    assert config.degiro_configuration.update_frequency_minutes == update_frequency_minutes


def test_config_default_without_config_file():
    BaseConfig.CONFIG_PATH = "tests/resources/stonks_overwatch/config/unexisting-config.json"

    config = Config.default()

    assert config.base_currency == "EUR"
    assert config.degiro_configuration.credentials is None
    assert config.degiro_configuration.start_date == DegiroConfig.DEFAULT_DEGIRO_START_DATE
    assert config.degiro_configuration.update_frequency_minutes == 5
