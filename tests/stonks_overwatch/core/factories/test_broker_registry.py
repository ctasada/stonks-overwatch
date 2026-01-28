"""
Tests for the BrokerRegistry.

This module contains comprehensive tests for the broker registry
functionality, including configuration and service registration, validation,
and error handling.
"""

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.base_credentials import BaseCredentials
from stonks_overwatch.core.factories.broker_registry import (
    BrokerRegistry,
    BrokerRegistryValidationError,
)
from stonks_overwatch.core.interfaces.deposit_service import DepositServiceInterface
from stonks_overwatch.core.interfaces.dividend_service import DividendServiceInterface
from stonks_overwatch.core.interfaces.portfolio_service import PortfolioServiceInterface
from stonks_overwatch.core.interfaces.transaction_service import TransactionServiceInterface
from stonks_overwatch.core.service_types import ServiceType

import pytest


# Test fixtures
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
        return self.username and self.password

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

    def __init__(self, credentials: MockCredentials = None, enabled: bool = True):
        credentials = credentials or MockCredentials()
        super().__init__(credentials, enabled)

    def is_enabled(self) -> bool:
        """Check if the broker is enabled."""
        return self.enabled

    def is_valid(self) -> bool:
        """Check if the configuration is valid."""
        return self.enabled and self.credentials and self.credentials.is_valid()

    def get_credentials(self) -> MockCredentials:
        """Get the broker credentials."""
        return self.credentials

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


class MockPortfolioService(PortfolioServiceInterface):
    """Mock portfolio service for testing."""

    def __init__(self, config: MockBrokerConfig = None):
        self.config = config

    def get_portfolio(self):
        return {"holdings": []}


class MockTransactionService(TransactionServiceInterface):
    """Mock transaction service for testing."""

    def __init__(self, config: MockBrokerConfig = None):
        self.config = config

    def get_transactions(self):
        return {"transactions": []}


class MockDepositService(DepositServiceInterface):
    """Mock deposit service for testing."""

    def __init__(self, config: MockBrokerConfig = None):
        self.config = config

    def get_deposits(self):
        return {"deposits": []}


class MockDividendService(DividendServiceInterface):
    """Mock dividend service for testing."""

    def __init__(self, config: MockBrokerConfig = None):
        self.config = config

    def get_dividends(self):
        return {"dividends": []}


@pytest.fixture(autouse=True)
def clear_singletons():
    """Clear singleton instances before each test."""
    # Clear singleton instances
    if hasattr(BrokerRegistry, "_instances"):
        BrokerRegistry._instances.clear()


class TestBrokerRegistry:
    """Test cases for BrokerRegistry."""

    def setup_method(self):
        """Set up test environment."""
        # Clear singleton instances
        if hasattr(BrokerRegistry, "_instances"):
            BrokerRegistry._instances.clear()
        self.registry = BrokerRegistry()
        # Clear any existing registrations
        self.registry.clear_all_registrations()

    def test_registry_is_singleton(self):
        """Test that registry follows singleton pattern."""
        registry1 = BrokerRegistry()
        registry2 = BrokerRegistry()
        assert registry1 is registry2

    def test_register_broker_config_success(self):
        """Test successful broker configuration registration."""
        self.registry.register_broker_config("testbroker", MockBrokerConfig)

        assert self.registry.is_config_registered("testbroker")
        assert self.registry.get_config_class("testbroker") == MockBrokerConfig

    def test_register_broker_config_invalid_class(self):
        """Test broker configuration registration with invalid config class."""
        with pytest.raises(BrokerRegistryValidationError, match="config_class must be a class type"):
            self.registry.register_broker_config("testbroker", "not_a_class")

        with pytest.raises(BrokerRegistryValidationError, match="config_class must be a subclass of BaseConfig"):
            self.registry.register_broker_config("testbroker", str)

    def test_register_broker_config_duplicate(self):
        """Test duplicate broker configuration registration."""
        self.registry.register_broker_config("testbroker", MockBrokerConfig)

        with pytest.raises(
            BrokerRegistryValidationError, match="Configuration for broker 'testbroker' is already registered"
        ):
            self.registry.register_broker_config("testbroker", MockBrokerConfig)

    def test_get_config_class_nonexistent(self):
        """Test getting configuration class for non-existent broker."""
        config_class = self.registry.get_config_class("nonexistent")
        assert config_class is None

    def test_register_broker_services_success(self):
        """Test successful broker services registration."""
        self.registry.register_broker_services(
            "testbroker",
            portfolio=MockPortfolioService,
            transaction=MockTransactionService,
            deposit=MockDepositService,
            dividend=MockDividendService,
        )

        assert self.registry.get_service_class("testbroker", ServiceType.PORTFOLIO) == MockPortfolioService
        assert self.registry.get_service_class("testbroker", ServiceType.TRANSACTION) == MockTransactionService
        assert self.registry.get_service_class("testbroker", ServiceType.DEPOSIT) == MockDepositService
        assert self.registry.get_service_class("testbroker", ServiceType.DIVIDEND) == MockDividendService

    def test_register_broker_services_missing_required(self):
        """Test broker services registration missing required services."""
        with pytest.raises(BrokerRegistryValidationError, match="Missing required services"):
            self.registry.register_broker_services(
                "testbroker",
                transaction=MockTransactionService,
                deposit=MockDepositService,
            )

    def test_register_broker_services_invalid_service_type(self):
        """Test broker services registration with invalid service type."""
        with pytest.raises(BrokerRegistryValidationError, match="Invalid service type"):
            self.registry.register_broker_services(
                "testbroker",
                portfolio=MockPortfolioService,
                invalid_service=MockTransactionService,
            )

    def test_register_broker_services_invalid_service_class(self):
        """Test broker services registration with invalid service class."""
        with pytest.raises(BrokerRegistryValidationError, match="Service .* must be a class type"):
            self.registry.register_broker_services(
                "testbroker",
                portfolio="not_a_class",
            )

    def test_register_broker_services_no_services(self):
        """Test broker services registration with no services."""
        with pytest.raises(BrokerRegistryValidationError, match="At least one service must be provided"):
            self.registry.register_broker_services("testbroker")

    def test_register_broker_services_duplicate(self):
        """Test duplicate broker services registration."""
        self.registry.register_broker_services("testbroker", portfolio=MockPortfolioService)

        with pytest.raises(
            BrokerRegistryValidationError, match="Services for broker 'testbroker' are already registered"
        ):
            self.registry.register_broker_services("testbroker", portfolio=MockPortfolioService)

    def test_get_service_class_nonexistent_broker(self):
        """Test getting service class for non-existent broker."""
        service_class = self.registry.get_service_class("nonexistent", ServiceType.PORTFOLIO)
        assert service_class is None

    def test_get_service_class_nonexistent_service(self):
        """Test getting non-existent service class for broker."""
        self.registry.register_broker_services("testbroker", portfolio=MockPortfolioService)

        service_class = self.registry.get_service_class("testbroker", ServiceType.DIVIDEND)
        assert service_class is None

    def test_broker_supports_service(self):
        """Test checking if broker supports specific service."""
        self.registry.register_broker_services(
            "testbroker",
            portfolio=MockPortfolioService,
            transaction=MockTransactionService,
        )

        assert self.registry.broker_supports_service("testbroker", ServiceType.PORTFOLIO)
        assert self.registry.broker_supports_service("testbroker", ServiceType.TRANSACTION)
        assert not self.registry.broker_supports_service("testbroker", ServiceType.DIVIDEND)
        assert not self.registry.broker_supports_service("nonexistent", ServiceType.PORTFOLIO)

    def test_get_broker_capabilities(self):
        """Test getting broker capabilities."""
        self.registry.register_broker_services(
            "testbroker",
            portfolio=MockPortfolioService,
            transaction=MockTransactionService,
        )

        capabilities = self.registry.get_broker_capabilities("testbroker")
        assert ServiceType.PORTFOLIO in capabilities
        assert ServiceType.TRANSACTION in capabilities
        assert ServiceType.DIVIDEND not in capabilities

        # Test non-existent broker
        empty_capabilities = self.registry.get_broker_capabilities("nonexistent")
        assert empty_capabilities == []

    def test_test_register_complete_broker_success(self):
        """Test successful complete broker registration."""
        self.registry.register_complete_broker(
            "testbroker",
            MockBrokerConfig,
            portfolio=MockPortfolioService,
            transaction=MockTransactionService,
            deposit=MockDepositService,
        )

        assert self.registry.is_config_registered("testbroker")
        assert self.registry.get_config_class("testbroker") == MockBrokerConfig
        assert self.registry.get_service_class("testbroker", ServiceType.PORTFOLIO) == MockPortfolioService
        assert self.registry.get_service_class("testbroker", ServiceType.TRANSACTION) == MockTransactionService
        assert self.registry.get_service_class("testbroker", ServiceType.DEPOSIT) == MockDepositService

    def test_test_register_complete_broker_rollback_on_service_failure(self):
        """Test rollback of config registration when service registration fails."""
        with pytest.raises(BrokerRegistryValidationError, match="Missing required services"):
            self.registry.register_complete_broker(
                "testbroker",
                MockBrokerConfig,
                transaction=MockTransactionService,  # Missing required portfolio service
            )

        # Configuration should not be registered due to rollback
        assert not self.registry.is_config_registered("testbroker")

    def test_get_registered_brokers(self):
        """Test getting list of registered brokers."""
        self.registry.register_broker_config("broker1", MockBrokerConfig)
        self.registry.register_broker_config("broker2", MockBrokerConfig)

        brokers = self.registry.get_registered_brokers()
        assert "broker1" in brokers
        assert "broker2" in brokers
        assert len(brokers) == 2

    def test_get_fully_registered_brokers(self):
        """Test getting brokers with both config and services."""
        # Register config only
        self.registry.register_broker_config("broker1", MockBrokerConfig)

        # Register complete broker
        self.registry.register_complete_broker(
            "broker2",
            MockBrokerConfig,
            portfolio=MockPortfolioService,
        )

        fully_registered = self.registry.get_fully_registered_brokers()
        assert "broker1" not in fully_registered
        assert "broker2" in fully_registered
        assert len(fully_registered) == 1

    def test_get_registration_status(self):
        """Test getting registration status for all brokers."""
        # Register config only
        self.registry.register_broker_config("broker1", MockBrokerConfig)

        # Register complete broker
        self.registry.register_complete_broker(
            "broker2",
            MockBrokerConfig,
            portfolio=MockPortfolioService,
        )

        status = self.registry.get_registration_status()

        assert status["broker1"]["config_registered"] is True
        assert status["broker1"]["services_registered"] is False

        assert status["broker2"]["config_registered"] is True
        assert status["broker2"]["services_registered"] is True

    def test_validate_all_registrations(self):
        """Test validation of all broker registrations."""
        # Register complete valid broker
        self.registry.register_complete_broker(
            "validbroker",
            MockBrokerConfig,
            portfolio=MockPortfolioService,
        )

        # Register config without services
        self.registry.register_broker_config("incompletebroker", MockBrokerConfig)

        validation = self.registry.validate_all_registrations()

        assert validation["all_valid"] is False
        assert validation["brokers"]["validbroker"]["valid"] is True
        assert validation["brokers"]["incompletebroker"]["valid"] is False
        assert "No services registered" in validation["brokers"]["incompletebroker"]["issues"]

    def test_unregister_broker(self):
        """Test unregistering a broker."""
        # Register complete broker
        self.registry.register_complete_broker(
            "testbroker",
            MockBrokerConfig,
            portfolio=MockPortfolioService,
        )

        assert self.registry.is_config_registered("testbroker")

        # Unregister broker
        result = self.registry.unregister_broker("testbroker")

        assert result is True
        assert not self.registry.is_config_registered("testbroker")
        assert self.registry.get_service_class("testbroker", ServiceType.PORTFOLIO) is None

        # Try unregistering non-existent broker
        result = self.registry.unregister_broker("nonexistent")
        assert result is False

    def test_clear_all_registrations(self):
        """Test clearing all registrations."""
        self.registry.register_complete_broker(
            "testbroker",
            MockBrokerConfig,
            portfolio=MockPortfolioService,
        )

        assert len(self.registry.get_registered_brokers()) > 0

        self.registry.clear_all_registrations()

        assert len(self.registry.get_registered_brokers()) == 0
        assert len(self.registry.get_fully_registered_brokers()) == 0

    def test_validate_broker_service_compatibility(self):
        """Test validation of broker service compatibility."""
        # Register complete broker
        self.registry.register_complete_broker(
            "validbroker",
            MockBrokerConfig,
            portfolio=MockPortfolioService,
        )

        # Test valid broker
        result = self.registry.validate_broker_service_compatibility("validbroker")
        assert result["valid"] is True
        assert len(result["issues"]) == 0

        # Test broker with no config
        result = self.registry.validate_broker_service_compatibility("nonexistent")
        assert result["valid"] is False
        assert "No configuration registered" in result["issues"]

        # Test broker with config but no services
        self.registry.register_broker_config("incompletebroker", MockBrokerConfig)
        result = self.registry.validate_broker_service_compatibility("incompletebroker")
        assert result["valid"] is False
        assert "No services registered" in result["issues"]

    def test_thread_safety(self):
        """Test thread safety of registry operations."""
        import time
        from concurrent.futures import ThreadPoolExecutor

        def register_broker(brokerid):
            """Register a broker in a thread."""
            try:
                time.sleep(0.01)  # Simulate some work
                self.registry.register_broker_config(f"broker{brokerid}", MockBrokerConfig)
                self.registry.register_broker_services(f"broker{brokerid}", portfolio=MockPortfolioService)
                return True
            except Exception:
                return False

        # Register brokers concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(register_broker, i) for i in range(50)]
            results = [future.result() for future in futures]

        # All registrations should succeed
        assert all(results)
        assert len(self.registry.get_registered_brokers()) == 50
        assert len(self.registry.get_fully_registered_brokers()) == 50

    def test_singleton_behavior(self):
        """Test that multiple registry instances are the same object."""
        registry1 = BrokerRegistry()
        registry2 = BrokerRegistry()
        assert registry1 is registry2
