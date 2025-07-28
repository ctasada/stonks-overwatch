import pathlib
from datetime import datetime

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.bitvavo import BitvavoCredentials
from stonks_overwatch.config.config import Config
from stonks_overwatch.config.degiro import DegiroConfig, DegiroCredentials
from stonks_overwatch.core.factories.unified_broker_factory import UnifiedBrokerFactory
from stonks_overwatch.services.models import PortfolioId

import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def disable_config_caching():
    """Disable config caching for all tests to ensure fresh config loading."""
    factory = UnifiedBrokerFactory()
    factory.disable_caching()
    yield
    factory.enable_caching()


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
    assert config.registry.get_broker_config("degiro").credentials == credentials
    assert config.registry.get_broker_config("degiro").start_date == start_date_as_date


def test_config_init_invalid_base_currency():
    """Test initialization with invalid base currency type."""
    with pytest.raises(TypeError, match="base_currency must be a string"):
        Config(base_currency=123)


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
        "degiro": {"credentials": credentials_dict, "start_date": start_date},
    }

    config = Config.from_dict(config_dict)

    assert config.base_currency == base_currency
    assert config.registry.get_broker_config("degiro").credentials == DegiroCredentials.from_dict(credentials_dict)
    assert config.registry.get_broker_config("degiro").start_date == start_date_as_date


def test_config_from_dict_empty():
    """Test loading configuration from empty dictionary."""
    config = Config.from_dict({})
    assert config.base_currency == Config.DEFAULT_BASE_CURRENCY
    assert config.registry.get_broker_config("degiro") is not None
    assert config.registry.get_broker_config("bitvavo") is not None


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
    assert config.registry.get_broker_config("degiro").credentials == DegiroCredentials.from_dict(credentials_dict)
    assert config.registry.get_broker_config("degiro").start_date == start_date_as_date
    assert config.registry.get_broker_config("degiro").update_frequency_minutes == update_frequency_minutes


def test_config_from_json_file_invalid():
    """Test loading configuration from an invalid JSON file."""
    with pytest.raises(FileNotFoundError):
        Config.from_json_file("tests/resources/stonks_overwatch/config/invalid-config.json")


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

    config = Config._default()

    assert config.base_currency == base_currency
    assert config.registry.get_broker_config("degiro").credentials == DegiroCredentials.from_dict(credentials_dict)
    assert config.registry.get_broker_config("degiro").start_date == start_date_as_date
    assert config.registry.get_broker_config("degiro").update_frequency_minutes == update_frequency_minutes


def test_config_default_without_config_file():
    BaseConfig.CONFIG_PATH = "tests/resources/stonks_overwatch/config/unexisting-config.json"

    config = Config._default()

    assert config.base_currency == "EUR"
    assert config.registry.get_broker_config("degiro").credentials is None
    assert config.registry.get_broker_config("degiro").start_date == DegiroConfig.DEFAULT_DEGIRO_START_DATE
    assert config.registry.get_broker_config("degiro").update_frequency_minutes == 5


def test_config_portfolio_status():
    """Test portfolio status checks."""
    config = Config._default()

    # Patch DeGiroService.check_connection to avoid real connection attempts
    with patch(
        "stonks_overwatch.services.brokers.degiro.client.degiro_client.DeGiroService.check_connection",
        return_value=True,
    ):
        # Test DeGiro portfolio status
        assert config.is_enabled(PortfolioId.DEGIRO) == config.is_degiro_enabled()
        assert config.is_enabled_and_connected(PortfolioId.DEGIRO) == config.is_degiro_enabled_and_connected()

        # Test Bitvavo portfolio status
        assert config.is_enabled(PortfolioId.BITVAVO) == config.is_bitvavo_enabled()
        # Bitvavo doesn't have connection checking, so it should be the same as enabled
        assert config.is_enabled_and_connected(PortfolioId.BITVAVO) == config.is_bitvavo_enabled()

        # Test invalid portfolio
        assert not config.is_enabled("INVALID_PORTFOLIO")
        assert not config.is_enabled_and_connected("INVALID_PORTFOLIO")


def test_config_degiro_status():
    """Test DeGiro-specific status checks."""
    config = Config._default()

    # Test with DeGiro portfolio
    assert config.is_degiro_enabled(PortfolioId.DEGIRO)
    assert config.is_degiro_enabled(PortfolioId.ALL)
    assert not config.is_degiro_enabled(PortfolioId.BITVAVO)

    # Test connection status
    with patch(
        "stonks_overwatch.services.brokers.degiro.client.degiro_client.DeGiroService.check_connection",
        return_value=True,
    ):
        assert config.is_degiro_connected()
        assert config.is_degiro_enabled_and_connected()

    with patch(
        "stonks_overwatch.services.brokers.degiro.client.degiro_client.DeGiroService.check_connection",
        return_value=False,
    ):
        assert not config.is_degiro_connected()
        assert not config.is_degiro_enabled_and_connected()


def test_config_bitvavo_status():
    """Test Bitvavo-specific status checks."""
    # Create a fresh config without loading from test file to test default behavior
    config = Config.from_dict({})

    # Test with Bitvavo portfolio - should be disabled by default because no credentials
    assert not config.is_bitvavo_enabled(PortfolioId.BITVAVO)
    assert not config.is_bitvavo_enabled(PortfolioId.ALL)
    assert not config.is_bitvavo_enabled(PortfolioId.DEGIRO)

    # Test with disabled configuration
    config.registry.get_broker_config("bitvavo").enabled = False
    assert not config.is_bitvavo_enabled()

    # Test with missing credentials
    config.registry.get_broker_config("bitvavo").enabled = True
    config.registry.get_broker_config("bitvavo").credentials = None
    assert not config.is_bitvavo_enabled()

    # Test with Bitvavo Credentials
    config.registry.get_broker_config("bitvavo").enabled = True
    config.registry.get_broker_config("bitvavo").credentials = BitvavoCredentials(apikey="key", apisecret="secret")
    assert config.is_bitvavo_enabled()


def test_config_equality():
    """Test configuration equality checks."""
    config1 = Config._default()
    config2 = Config._default()
    assert config1 == config2

    # Test with different base currency
    config2.base_currency = "USD"
    assert config1 != config2

    # Test with different DeGiro configuration
    config2 = Config._default()
    from stonks_overwatch.config.degiro import DegiroConfig

    new_degiro_config = DegiroConfig(credentials=None, start_date=DegiroConfig.DEFAULT_DEGIRO_START_DATE, enabled=False)
    config2.registry.set_broker_config("degiro", new_degiro_config)
    assert config1 != config2

    # Test with different Bitvavo configuration
    config3 = Config._default()
    from stonks_overwatch.config.bitvavo import BitvavoConfig

    new_bitvavo_config = BitvavoConfig(credentials=None, enabled=False)
    config3.registry.set_broker_config("bitvavo", new_bitvavo_config)
    assert config1 != config3

    # Test with non-Config object
    assert config1 != "not a config"


def test_config_repr():
    """Test configuration string representation."""
    config = Config._default()
    repr_str = repr(config)
    assert "Config" in repr_str
    assert "base_currency" in repr_str
    assert "degiro" in repr_str
    assert "bitvavo" in repr_str
