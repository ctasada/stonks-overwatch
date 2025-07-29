import pathlib

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.config import Config
from stonks_overwatch.core.factories.broker_factory import BrokerFactory
from stonks_overwatch.services.models import PortfolioId

import pytest


@pytest.fixture(autouse=True)
def disable_config_caching():
    """Disable config caching for all tests to ensure fresh config loading."""
    factory = BrokerFactory()
    factory.disable_caching()
    yield
    factory.enable_caching()


def test_config_init():
    """Test Config initialization with base currency."""
    base_currency = "USD"

    config = Config(base_currency=base_currency)

    # Test that base currency is set correctly
    assert config.base_currency == base_currency

    # Test that broker configs can be retrieved via the unified factory
    degiro_config = config.get_broker_config("degiro")
    assert degiro_config is not None
    assert isinstance(degiro_config, BaseConfig)

    # Test with default base currency
    default_config = Config()
    assert default_config.base_currency == "EUR"  # DEFAULT_BASE_CURRENCY


def test_config_init_invalid_base_currency():
    """Test initialization with invalid base currency type."""
    with pytest.raises(TypeError, match="base_currency must be a string"):
        Config(base_currency=123)


def test_config_from_dict():
    """Test loading configuration from dictionary."""
    base_currency = "USD"
    config_dict = {"base_currency": base_currency}

    config = Config.from_dict(config_dict)

    assert config.base_currency == base_currency
    # Broker configs are loaded on-demand via BrokerFactory
    degiro_config = config.get_broker_config("degiro")
    assert degiro_config is not None


def test_config_from_dict_empty():
    """Test loading configuration from empty dictionary."""
    config = Config.from_dict({})
    assert config.base_currency == Config.DEFAULT_BASE_CURRENCY
    # Broker configs are available via unified factory
    assert config.get_broker_config("degiro") is not None


def test_config_from_json_file():
    """Test loading configuration from JSON file."""
    file = pathlib.Path("tests/resources/stonks_overwatch/config/sample-config.json")
    config = Config.from_json_file(file)

    assert config.base_currency == "EUR"  # From sample config file
    # Verify broker configs can be loaded
    assert config.get_broker_config("degiro") is not None


def test_config_from_json_file_invalid():
    """Test loading configuration from an invalid JSON file."""
    with pytest.raises(FileNotFoundError):
        Config.from_json_file("tests/resources/stonks_overwatch/config/invalid-config.json")


def test_config_default():
    """Test default configuration creation."""
    config = Config._default()

    assert config.base_currency == "EUR"
    # Verify broker configs are available via unified factory
    assert config.get_broker_config("degiro") is not None
    assert config.get_broker_config("bitvavo") is not None


def test_config_default_without_config_file():
    """Test default configuration when config file doesn't exist."""
    config = Config._default()

    assert config.base_currency == "EUR"
    # Even without config file, broker configs should be available via defaults
    assert config.get_broker_config("degiro") is not None


def test_config_portfolio_status():
    """Test portfolio status checks using unified API."""
    config = Config._default()

    # Test unified is_enabled method
    assert isinstance(config.is_enabled(PortfolioId.ALL), bool)
    assert isinstance(config.is_enabled(PortfolioId.DEGIRO), bool)
    assert isinstance(config.is_enabled(PortfolioId.BITVAVO), bool)


def test_config_degiro_status():
    """Test DeGiro status using unified API."""
    config = Config._default()

    # Test DeGiro via unified API
    degiro_enabled = config.is_enabled(PortfolioId.DEGIRO)
    assert isinstance(degiro_enabled, bool)

    # Test getting DeGiro config directly
    degiro_config = config.get_broker_config("degiro")
    assert degiro_config is not None


def test_config_bitvavo_status():
    """Test Bitvavo status using unified API."""
    config = Config.from_dict({})

    # Test Bitvavo via unified API
    bitvavo_enabled = config.is_enabled(PortfolioId.BITVAVO)
    assert isinstance(bitvavo_enabled, bool)

    # Test getting Bitvavo config directly
    bitvavo_config = config.get_broker_config("bitvavo")
    assert bitvavo_config is not None


def test_config_equality():
    """Test configuration equality checks."""
    config1 = Config._default()
    config2 = Config._default()
    assert config1 == config2

    # Test with different base currency
    config3 = Config(base_currency="USD")
    assert config1 != config3


def test_config_repr():
    """Test configuration string representation."""
    config = Config._default()
    repr_str = repr(config)
    assert "Config" in repr_str
    assert "base_currency" in repr_str
    assert "degiro" in repr_str
    assert "bitvavo" in repr_str
