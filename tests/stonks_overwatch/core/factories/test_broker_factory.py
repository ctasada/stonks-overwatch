"""
Tests for the BrokerFactory.

This module contains comprehensive tests for the broker factory
functionality, including configuration creation, service creation with
dependency injection, caching, and error handling.
"""

from datetime import date

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.base_credentials import BaseCredentials
from stonks_overwatch.core.factories.broker_factory import (
    BrokerFactory,
    BrokerFactoryError,
)
from stonks_overwatch.core.factories.broker_registry import (
    BrokerRegistry,
)
from stonks_overwatch.core.interfaces import (
    DepositServiceInterface,
    FeeServiceInterface,
    PortfolioServiceInterface,
    TransactionServiceInterface,
)
from stonks_overwatch.core.service_types import ServiceType
from stonks_overwatch.services.models import TotalPortfolio

import pytest


# Test fixtures (reuse from registry tests)
class MockCredentials(BaseCredentials):
    """Mock credentials for testing."""

    def __init__(self, username: str = "test", password: str = "pass"):
        self.username = username
        self.password = password

    def to_auth_params(self) -> dict:
        """Convert credentials to authentication parameters."""
        return {
            "username": self.username,
            "password": self.password,
        }

    def is_valid(self) -> bool:
        """Check if credentials are valid."""
        return bool(self.username and self.password)

    def to_dict(self) -> dict:
        """Convert credentials to dictionary."""
        return {
            "username": self.username,
            "password": self.password,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MockCredentials":
        """Create credentials from dictionary."""
        return cls(
            username=data.get("username", "test"),
            password=data.get("password", "pass"),
        )


class MockBrokerConfig(BaseConfig):
    """Mock broker configuration for testing."""

    config_key = "testbroker"

    def __init__(
        self,
        credentials: MockCredentials = None,
        enabled: bool = True,
        start_date: date = None,
        offline_mode: bool = False,
        update_frequency_minutes: int = 5,
    ):
        credentials = credentials or MockCredentials()
        if start_date is None:
            start_date = date.today()
        super().__init__(credentials, start_date, enabled, offline_mode, update_frequency_minutes)

    def is_enabled(self) -> bool:
        """Check if the broker is enabled."""
        return self.enabled

    def is_valid(self) -> bool:
        """Check if the configuration is valid."""
        return (
            self.enabled
            and self.credentials is not None
            and hasattr(self.credentials, "is_valid")
            and self.credentials.is_valid()
        )

    def get_credentials(self) -> MockCredentials:
        """Get the broker credentials."""
        return self.credentials if isinstance(self.credentials, MockCredentials) else None

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "enabled": self.enabled,
            "credentials": self.credentials.to_dict() if self.credentials else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MockBrokerConfig":
        """Create configuration from dictionary."""
        credentials_data = data.get("credentials", {})
        credentials = MockCredentials.from_dict(credentials_data) if credentials_data else None
        return cls(
            credentials=credentials,
            enabled=data.get("enabled", True),
        )

    @classmethod
    def default(cls) -> "MockBrokerConfig":
        """Create default configuration."""
        return cls(credentials=MockCredentials(), enabled=True)

    @classmethod
    def from_db_with_json_override(cls, broker_name: str) -> "MockBrokerConfig":
        """Override to avoid LazyConfig wrapper in tests."""
        return cls.default()


class MockPortfolioService(PortfolioServiceInterface):
    """Mock portfolio service for testing."""

    def __init__(self, config: MockBrokerConfig = None):
        self.config = config

    @property
    def get_portfolio(self):
        return []

    def get_portfolio_total(self, portfolio=None):
        # Provide all required parameters for TotalPortfolio
        return TotalPortfolio(
            base_currency="USD",
            total_pl=0.0,
            total_cash=0.0,
            current_value=0.0,
            total_roi=0.0,
            total_deposit_withdrawal=0.0,
        )

    def calculate_historical_value(self):
        return []

    def calculate_product_growth(self):
        return {}


class MockTransactionService(TransactionServiceInterface):
    """Mock transaction service for testing."""

    def __init__(self, config: MockBrokerConfig = None):
        self.config = config

    def get_transactions(self):
        return []


class MockDepositService(DepositServiceInterface):
    """Mock deposit service for testing."""

    def __init__(self, config: MockBrokerConfig = None):
        self.config = config

    def get_cash_deposits(self):
        return []

    def calculate_cash_account_value(self):
        return {}


@pytest.fixture(autouse=True)
def clear_singletons():
    """Clear singleton instances before each test."""
    # Clear singleton instances
    if hasattr(BrokerFactory, "_instances"):
        BrokerFactory._instances.clear()
    if hasattr(BrokerRegistry, "_instances"):
        BrokerRegistry._instances.clear()


class TestBrokerFactory:
    """Test cases for BrokerFactory."""

    def setup_method(self):
        """Set up test environment."""
        # Clear singleton instances
        if hasattr(BrokerFactory, "_instances"):
            BrokerFactory._instances.clear()
        if hasattr(BrokerRegistry, "_instances"):
            BrokerRegistry._instances.clear()

        self.registry = BrokerRegistry()
        # Clear any existing registrations
        self.registry.clear_all_registrations()
        self.factory = BrokerFactory()

        # Register test broker
        self.registry.register_broker_config("testbroker", MockBrokerConfig)
        self.registry.register_broker_services(
            "testbroker",
            portfolio=MockPortfolioService,
            transaction=MockTransactionService,
            deposit=MockDepositService,
        )

    def test_factory_is_singleton(self):
        """Test that factory follows singleton pattern."""
        factory1 = BrokerFactory()
        factory2 = BrokerFactory()
        assert factory1 is factory2

    def test_create_config_with_defaults(self):
        """Test creating configuration with default values."""
        config = self.factory.create_config("testbroker")

        assert config is not None
        assert isinstance(config, MockBrokerConfig)
        assert config.is_enabled()
        credentials = config.get_credentials() if hasattr(config, "get_credentials") else config.credentials
        assert credentials is not None
        assert getattr(credentials, "username", None) == "test"

    def test_create_config_with_kwargs(self):
        """Test creating configuration with custom kwargs."""
        custom_credentials = MockCredentials(username="custom", password="secret")
        config = self.factory.create_config("testbroker", credentials=custom_credentials, enabled=False)

        assert config is not None
        assert isinstance(config, MockBrokerConfig)
        assert not config.is_enabled()
        credentials = config.get_credentials() if hasattr(config, "get_credentials") else config.credentials
        assert credentials is not None
        assert getattr(credentials, "username", None) == "custom"

    def test_create_config_caching(self):
        """Test that default configs are cached."""
        config1 = self.factory.create_config("testbroker")
        config2 = self.factory.create_config("testbroker")

        assert config1 is config2

    def test_create_config_no_caching_with_kwargs(self):
        """Test that configs with custom kwargs are not cached."""
        config1 = self.factory.create_config("testbroker", enabled=False)
        config2 = self.factory.create_config("testbroker", enabled=False)

        assert config1 is not config2

    def test_create_config_nonexistent_broker(self):
        """Test creating configuration for non-existent broker."""
        config = self.factory.create_config("nonexistent")
        assert config is None

    def test_create_config_error_handling(self):
        """Test error handling in config creation."""

        # Create a config class that raises an exception and doesn't have from_db_with_json_override
        class FailingConfig(BaseConfig):
            def __init__(self, **kwargs):
                super().__init__(None, date.today())
                raise ValueError("Config creation failed")

            @classmethod
            def default(cls):
                raise ValueError("Config creation failed")

            @classmethod
            def from_dict(cls, data: dict):
                raise ValueError("Config creation failed")

            @property
            def get_credentials(self):
                raise ValueError("Config creation failed")

        self.registry.register_broker_config("failingbroker", FailingConfig)

        # Use custom kwargs to bypass from_db_with_json_override and trigger direct construction
        with pytest.raises(BrokerFactoryError, match="Failed to create configuration"):
            self.factory.create_config("failingbroker", enabled=True)

    def test_create_default_config(self):
        """Test creating default configuration."""
        config = self.factory.create_default_config("testbroker")

        assert config is not None
        assert isinstance(config, MockBrokerConfig)
        assert config.is_enabled()

    def test_create_default_config_nonexistent_broker(self):
        """Test creating default config for non-existent broker."""
        config = self.factory.create_default_config("nonexistent")
        assert config is None

    def test_create_default_config_error_handling(self):
        """Test error handling in default config creation."""

        # Create a config class without default method
        class NoDefaultConfig(BaseConfig):
            def __init__(self):
                super().__init__(None, date.today())
                # Empty init for testing purposes - missing required default() method
                pass

            @classmethod
            def from_dict(cls, data: dict):
                return cls(None, date.today())

            @property
            def get_credentials(self):
                return None

        self.registry.register_broker_config("nodefaultbroker", NoDefaultConfig)

        with pytest.raises(BrokerFactoryError, match="Failed to create default configuration"):
            self.factory.create_default_config("nodefaultbroker")

    def test_create_config_from_dict(self):
        """Test creating configuration from dictionary."""
        data = {
            "enabled": False,
            "credentials": {"username": "dict_user", "password": "dict_pass"},
        }

        config = self.factory.create_config_from_dict("testbroker", data)

        assert config is not None
        assert isinstance(config, MockBrokerConfig)
        assert not config.is_enabled()
        credentials = config.get_credentials() if hasattr(config, "get_credentials") else config.credentials
        assert credentials is not None
        assert getattr(credentials, "username", None) == "dict_user"

    def test_create_config_from_dict_nonexistent_broker(self):
        """Test creating config from dict for non-existent broker."""
        config = self.factory.create_config_from_dict("nonexistent", {})
        assert config is None

    def test_create_config_from_dict_error_handling(self):
        """Test error handling in config creation from dict."""

        # Register a failing config class
        class FailingConfig(BaseConfig):
            @classmethod
            def from_dict(cls, data: dict):
                raise ValueError("Failed to parse dict")

            @property
            def get_credentials(self):
                raise ValueError("Failed to get credentials")

        self.registry.register_broker_config("failingconfig", FailingConfig)

        with pytest.raises(BrokerFactoryError, match="Failed to create configuration from dict"):
            self.factory.create_config_from_dict("failingconfig", {})

    def test_create_service_with_dependency_injection(self):
        """Test creating service with automatic config injection."""
        service = self.factory.create_service("testbroker", ServiceType.PORTFOLIO)

        assert service is not None
        assert isinstance(service, MockPortfolioService)
        assert service.config is not None
        assert isinstance(service.config, MockBrokerConfig)

    def test_create_service_with_custom_config(self):
        """Test creating service with custom config."""
        # Clear cache to ensure we create a fresh service
        self.factory.clear_cache("testbroker")

        custom_config = MockBrokerConfig(enabled=False)
        service = self.factory.create_service("testbroker", ServiceType.PORTFOLIO, config=custom_config)

        assert service is not None
        assert service.config is custom_config
        assert not service.config.is_enabled()

    def test_create_service_caching(self):
        """Test that services are cached."""
        service1 = self.factory.create_service("testbroker", ServiceType.PORTFOLIO)
        service2 = self.factory.create_service("testbroker", ServiceType.PORTFOLIO)

        assert service1 is service2

    def test_create_service_nonexistent_broker(self):
        """Test creating service for non-existent broker."""
        service = self.factory.create_service("nonexistent", ServiceType.PORTFOLIO)
        assert service is None

    def test_create_service_unsupported_service_type(self):
        """Test creating unsupported service type."""
        service = self.factory.create_service("testbroker", ServiceType.DIVIDEND)
        assert service is None

    def test_create_service_error_handling(self):
        """Test error handling in service creation."""

        # Create a service class that raises an exception but implements the interface
        class FailingService(FeeServiceInterface):
            def __init__(self, **kwargs):
                raise ValueError("Service creation failed")

            def get_fees(self):
                return []

        # Register a new broker with failing service
        self.registry.register_broker_config("failingservice", MockBrokerConfig)
        self.registry.register_broker_services("failingservice", portfolio=MockPortfolioService, fee=FailingService)

        with pytest.raises(BrokerFactoryError, match="Failed to create fee service"):
            self.factory.create_service("failingservice", ServiceType.FEE)

    def test_create_portfolio_service(self):
        """Test creating portfolio service with type checking."""
        service = self.factory.create_portfolio_service("testbroker")

        assert service is not None
        assert isinstance(service, MockPortfolioService)

    def test_create_portfolio_service_unsupported(self):
        """Test creating portfolio service for broker that doesn't support it."""
        # Register broker with portfolio service first (required by registry)
        self.registry.register_broker_config("noportfoliobroker", MockBrokerConfig)
        self.registry.register_broker_services(
            "noportfoliobroker", portfolio=MockPortfolioService, transaction=MockTransactionService
        )

        # Now manually remove the portfolio service to simulate unsupported service
        self.registry._service_classes["noportfoliobroker"].pop(ServiceType.PORTFOLIO, None)
        self.registry._broker_capabilities["noportfoliobroker"].remove(ServiceType.PORTFOLIO)

        with pytest.raises(BrokerFactoryError, match="does not support portfolio service"):
            self.factory.create_portfolio_service("noportfoliobroker")

    def test_create_transaction_service(self):
        """Test creating transaction service with type checking."""
        service = self.factory.create_transaction_service("testbroker")

        assert service is not None
        assert isinstance(service, MockTransactionService)

    def test_create_transaction_service_unsupported(self):
        """Test creating transaction service for broker that doesn't support it."""
        self.registry.register_broker_config("notransactionbroker", MockBrokerConfig)
        self.registry.register_broker_services(
            "notransactionbroker", portfolio=MockPortfolioService, transaction=MockTransactionService
        )

        # Remove transaction service to simulate unsupported service
        self.registry._service_classes["notransactionbroker"].pop(ServiceType.TRANSACTION, None)
        self.registry._broker_capabilities["notransactionbroker"].remove(ServiceType.TRANSACTION)

        with pytest.raises(BrokerFactoryError, match="does not support transaction service"):
            self.factory.create_transaction_service("notransactionbroker")

    def test_create_deposit_service(self):
        """Test creating deposit service with type checking."""
        service = self.factory.create_deposit_service("testbroker")

        assert service is not None
        assert isinstance(service, MockDepositService)

    def test_create_deposit_service_unsupported(self):
        """Test creating deposit service for broker that doesn't support it."""
        self.registry.register_broker_config("nodepositbroker", MockBrokerConfig)
        self.registry.register_broker_services(
            "nodepositbroker", portfolio=MockPortfolioService, deposit=MockDepositService
        )

        # Remove deposit service to simulate unsupported service
        self.registry._service_classes["nodepositbroker"].pop(ServiceType.DEPOSIT, None)
        self.registry._broker_capabilities["nodepositbroker"].remove(ServiceType.DEPOSIT)

        with pytest.raises(BrokerFactoryError, match="does not support deposit service"):
            self.factory.create_deposit_service("nodepositbroker")

    def test_create_dividend_service(self):
        """Test creating optional dividend service."""
        # Dividend service is not registered for testbroker
        service = self.factory.create_dividend_service("testbroker")
        assert service is None

    def test_create_fee_service(self):
        """Test creating optional fee service."""
        # Fee service is not registered for testbroker
        service = self.factory.create_fee_service("testbroker")
        assert service is None

    def test_create_account_service(self):
        """Test creating optional account service."""
        # Account service is not registered for testbroker
        service = self.factory.create_account_service("testbroker")
        assert service is None

    def test_create_all_services(self):
        """Test creating all services for a broker."""
        services = self.factory.create_all_services("testbroker")

        assert len(services) == 3
        assert ServiceType.PORTFOLIO in services
        assert ServiceType.TRANSACTION in services
        assert ServiceType.DEPOSIT in services

        assert isinstance(services[ServiceType.PORTFOLIO], MockPortfolioService)
        assert isinstance(services[ServiceType.TRANSACTION], MockTransactionService)
        assert isinstance(services[ServiceType.DEPOSIT], MockDepositService)

    def test_get_available_brokers(self):
        """Test getting available brokers."""
        brokers = self.factory.get_available_brokers()
        assert "testbroker" in brokers

    def test_is_broker_available(self):
        """Test checking if broker is available."""
        assert self.factory.is_broker_available("testbroker")
        assert not self.factory.is_broker_available("nonexistent")

    def test_get_broker_capabilities(self):
        """Test getting broker capabilities."""
        capabilities = self.factory.get_broker_capabilities("testbroker")
        assert ServiceType.PORTFOLIO in capabilities
        assert ServiceType.TRANSACTION in capabilities
        assert ServiceType.DEPOSIT in capabilities

    def test_broker_supports_service(self):
        """Test checking if broker supports specific service."""
        assert self.factory.broker_supports_service("testbroker", ServiceType.PORTFOLIO)
        assert self.factory.broker_supports_service("testbroker", ServiceType.TRANSACTION)
        assert not self.factory.broker_supports_service("testbroker", ServiceType.DIVIDEND)

    def test_clear_cache_specific_broker(self):
        """Test clearing cache for specific broker."""
        # Create some cached instances
        config = self.factory.create_config("testbroker")
        service = self.factory.create_service("testbroker", ServiceType.PORTFOLIO)

        # Clear cache for specific broker
        self.factory.clear_cache("testbroker")

        # New instances should be different
        new_config = self.factory.create_config("testbroker")
        new_service = self.factory.create_service("testbroker", ServiceType.PORTFOLIO)

        assert config is not new_config
        assert service is not new_service

    def test_clear_cache_all_brokers(self):
        """Test clearing cache for all brokers."""
        # Create some cached instances
        config = self.factory.create_config("testbroker")
        service = self.factory.create_service("testbroker", ServiceType.PORTFOLIO)

        # Clear all cache
        self.factory.clear_cache()

        # New instances should be different
        new_config = self.factory.create_config("testbroker")
        new_service = self.factory.create_service("testbroker", ServiceType.PORTFOLIO)

        assert config is not new_config
        assert service is not new_service

    def test_disable_caching(self):
        """Test disabling caching."""
        self.factory.disable_caching()

        # Instances should not be cached
        config1 = self.factory.create_config("testbroker")
        config2 = self.factory.create_config("testbroker")

        service1 = self.factory.create_service("testbroker", ServiceType.PORTFOLIO)
        service2 = self.factory.create_service("testbroker", ServiceType.PORTFOLIO)

        assert config1 is not config2
        assert service1 is not service2

    def test_enable_caching(self):
        """Test enabling caching."""
        self.factory.disable_caching()
        self.factory.enable_caching()

        # Instances should be cached again
        config1 = self.factory.create_config("testbroker")
        config2 = self.factory.create_config("testbroker")

        service1 = self.factory.create_service("testbroker", ServiceType.PORTFOLIO)
        service2 = self.factory.create_service("testbroker", ServiceType.PORTFOLIO)

        assert config1 is config2
        assert service1 is service2

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        # Create some instances
        self.factory.create_config("testbroker")
        self.factory.create_service("testbroker", ServiceType.PORTFOLIO)
        self.factory.create_service("testbroker", ServiceType.TRANSACTION)

        stats = self.factory.get_cache_stats()

        assert stats["cache_enabled"] is True
        assert "testbroker" in stats["cached_configs"]
        assert "testbroker" in stats["cached_services"]
        assert stats["total_config_instances"] == 1
        assert stats["total_service_instances"] == 2

    def test_singleton_behavior(self):
        """Test that multiple factory instances are the same object."""
        factory1 = BrokerFactory()
        factory2 = BrokerFactory()
        assert factory1 is factory2
