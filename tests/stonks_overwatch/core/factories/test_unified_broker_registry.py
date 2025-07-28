"""
Tests for the UnifiedBrokerRegistry.

This module contains comprehensive tests for the unified broker registry
functionality, including configuration and service registration, validation,
and error handling.
"""

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.base_credentials import BaseCredentials
from stonks_overwatch.core.factories.unified_broker_registry import (
    BrokerRegistryValidationError,
    UnifiedBrokerRegistry,
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


class MockConfig(BaseConfig):
    """Mock configuration for testing."""

    config_key = "mock"

    def __init__(self, credentials=None, enabled=True):
        super().__init__(credentials, enabled)

    @property
    def get_credentials(self):
        return self.credentials

    @classmethod
    def default(cls):
        return cls(MockCredentials(), True)

    @classmethod
    def from_dict(cls, data):
        return cls.default()


class MockPortfolioService(PortfolioServiceInterface):
    """Mock portfolio service for testing."""

    pass


class MockTransactionService(TransactionServiceInterface):
    """Mock transaction service for testing."""

    pass


class MockDepositService(DepositServiceInterface):
    """Mock deposit service for testing."""

    pass


class MockDividendService(DividendServiceInterface):
    """Mock dividend service for testing."""

    pass


class MockAccountService:
    """Mock account service for testing."""

    pass


class MockFeeService:
    """Mock fee service for testing."""

    pass


class TestUnifiedBrokerRegistry:
    """Test cases for UnifiedBrokerRegistry."""

    def setup_method(self):
        """Set up test fixtures."""
        # Clear singleton state before each test
        if hasattr(UnifiedBrokerRegistry, "_instances"):
            UnifiedBrokerRegistry._instances.clear()
        self.registry = UnifiedBrokerRegistry()

    def teardown_method(self):
        """Clean up after each test."""
        self.registry.clear_all_registrations()

    # Configuration registration tests
    def test_register_broker_config_success(self):
        """Test successful broker configuration registration."""
        self.registry.register_broker_config("test_broker", MockConfig)

        assert self.registry.is_config_registered("test_broker")
        assert self.registry.get_config_class("test_broker") == MockConfig
        assert "test_broker" in self.registry.get_registered_config_brokers()

    def test_register_broker_config_duplicate_raises_error(self):
        """Test that registering duplicate config raises error."""
        self.registry.register_broker_config("test_broker", MockConfig)

        with pytest.raises(BrokerRegistryValidationError, match="already registered"):
            self.registry.register_broker_config("test_broker", MockConfig)

    def test_register_broker_config_invalid_name_raises_error(self):
        """Test that invalid broker names raise errors."""
        invalid_names = [
            "",  # Empty
            "Test",  # Uppercase
            "test-broker",  # Hyphen
            "test broker",  # Space
            "test@broker",  # Special character
            123,  # Not string
            None,  # None
        ]

        for invalid_name in invalid_names:
            with pytest.raises(BrokerRegistryValidationError):
                self.registry.register_broker_config(invalid_name, MockConfig)

    def test_register_broker_config_invalid_class_raises_error(self):
        """Test that invalid config classes raise errors."""
        invalid_classes = [
            str,  # Not BaseConfig subclass
            123,  # Not a class
            None,  # None
            "not_a_class",  # String
        ]

        for invalid_class in invalid_classes:
            with pytest.raises(BrokerRegistryValidationError):
                self.registry.register_broker_config("test_broker", invalid_class)

    def test_get_config_class_nonexistent_returns_none(self):
        """Test that getting nonexistent config returns None."""
        assert self.registry.get_config_class("nonexistent") is None

    # Service registration tests
    def test_register_broker_services_success(self):
        """Test successful broker service registration."""
        services = {
            "portfolio": MockPortfolioService,
            "transaction": MockTransactionService,
            "deposit": MockDepositService,
        }

        self.registry.register_broker_services("test_broker", **services)

        assert self.registry.is_service_registered("test_broker")
        assert self.registry.get_service_class("test_broker", ServiceType.PORTFOLIO) == MockPortfolioService
        assert self.registry.get_service_class("test_broker", ServiceType.TRANSACTION) == MockTransactionService
        assert self.registry.get_service_class("test_broker", ServiceType.DEPOSIT) == MockDepositService
        assert "test_broker" in self.registry.get_registered_service_brokers()

    def test_register_broker_services_with_optional_services(self):
        """Test registering services with optional services."""
        services = {
            "portfolio": MockPortfolioService,
            "transaction": MockTransactionService,
            "deposit": MockDepositService,
            "dividend": MockDividendService,
            "fee": MockFeeService,
            "account": MockAccountService,
        }

        self.registry.register_broker_services("test_broker", **services)

        capabilities = self.registry.get_broker_capabilities("test_broker")
        assert ServiceType.PORTFOLIO in capabilities
        assert ServiceType.TRANSACTION in capabilities
        assert ServiceType.DEPOSIT in capabilities
        assert ServiceType.DIVIDEND in capabilities
        assert ServiceType.FEE in capabilities
        assert ServiceType.ACCOUNT in capabilities

    def test_register_broker_services_duplicate_raises_error(self):
        """Test that registering duplicate services raises error."""
        services = {
            "portfolio": MockPortfolioService,
            "transaction": MockTransactionService,
            "deposit": MockDepositService,
        }

        self.registry.register_broker_services("test_broker", **services)

        with pytest.raises(BrokerRegistryValidationError, match="already registered"):
            self.registry.register_broker_services("test_broker", **services)

    def test_register_broker_services_missing_required_raises_error(self):
        """Test that missing required services raises error."""
        incomplete_services = [
            {"transaction": MockTransactionService, "deposit": MockDepositService},  # Missing portfolio
        ]

        for services in incomplete_services:
            with pytest.raises(BrokerRegistryValidationError, match="missing required services"):
                self.registry.register_broker_services("test_broker", **services)

    def test_register_broker_services_portfolio_only_succeeds(self):
        """Test that portfolio-only service registration succeeds (like IBKR)."""
        # This should succeed with new flexible validation
        services = {"portfolio": MockPortfolioService}
        self.registry.register_broker_services("test_broker_minimal", **services)

        # Verify it was registered
        assert self.registry.is_service_registered("test_broker_minimal")
        capabilities = self.registry.get_broker_capabilities("test_broker_minimal")
        assert ServiceType.PORTFOLIO in capabilities
        assert len(capabilities) == 1

    def test_register_broker_services_invalid_service_type_raises_error(self):
        """Test that invalid service types raise errors."""
        services = {
            "portfolio": MockPortfolioService,
            "transaction": MockTransactionService,
            "deposit": MockDepositService,
            "invalid_service": MockPortfolioService,  # Invalid service type
        }

        with pytest.raises(BrokerRegistryValidationError, match="Unknown service type"):
            self.registry.register_broker_services("test_broker", **services)

    def test_register_broker_services_invalid_service_class_raises_error(self):
        """Test that invalid service classes raise errors."""
        services = {
            "portfolio": "not_a_class",
            "transaction": MockTransactionService,
            "deposit": MockDepositService,
        }

        with pytest.raises(BrokerRegistryValidationError, match="must be a class type"):
            self.registry.register_broker_services("test_broker", **services)

    def test_register_broker_services_empty_raises_error(self):
        """Test that empty services dict raises error."""
        with pytest.raises(BrokerRegistryValidationError, match="At least one service must be provided"):
            self.registry.register_broker_services("test_broker")

    def test_broker_supports_service(self):
        """Test broker service support checking."""
        services = {
            "portfolio": MockPortfolioService,
            "transaction": MockTransactionService,
            "deposit": MockDepositService,
        }

        self.registry.register_broker_services("test_broker", **services)

        assert self.registry.broker_supports_service("test_broker", ServiceType.PORTFOLIO)
        assert self.registry.broker_supports_service("test_broker", ServiceType.TRANSACTION)
        assert self.registry.broker_supports_service("test_broker", ServiceType.DEPOSIT)
        assert not self.registry.broker_supports_service("test_broker", ServiceType.DIVIDEND)
        assert not self.registry.broker_supports_service("nonexistent", ServiceType.PORTFOLIO)

    def test_get_service_class_nonexistent_returns_none(self):
        """Test that getting nonexistent service returns None."""
        assert self.registry.get_service_class("nonexistent", ServiceType.PORTFOLIO) is None

    # Unified methods tests
    def test_register_complete_broker_success(self):
        """Test successful complete broker registration."""
        services = {
            "portfolio": MockPortfolioService,
            "transaction": MockTransactionService,
            "deposit": MockDepositService,
        }

        self.registry.register_complete_broker("test_broker", MockConfig, **services)

        assert self.registry.is_fully_registered("test_broker")
        assert self.registry.get_config_class("test_broker") == MockConfig
        assert self.registry.get_service_class("test_broker", ServiceType.PORTFOLIO) == MockPortfolioService

    def test_register_complete_broker_service_failure_rollback(self):
        """Test that service registration failure rolls back config registration."""
        invalid_services = {
            "portfolio": "not_a_class",  # Invalid service
            "transaction": MockTransactionService,
            "deposit": MockDepositService,
        }

        with pytest.raises(BrokerRegistryValidationError):
            self.registry.register_complete_broker("test_broker", MockConfig, **invalid_services)

        # Config should be rolled back
        assert not self.registry.is_config_registered("test_broker")
        assert not self.registry.is_service_registered("test_broker")

    def test_get_fully_registered_brokers(self):
        """Test getting fully registered brokers."""
        # Register config only
        self.registry.register_broker_config("config_only", MockConfig)

        # Register services only
        services = {
            "portfolio": MockPortfolioService,
            "transaction": MockTransactionService,
            "deposit": MockDepositService,
        }
        self.registry.register_broker_services("services_only", **services)

        # Register both
        self.registry.register_complete_broker("complete", MockConfig, **services)

        fully_registered = self.registry.get_fully_registered_brokers()
        assert "complete" in fully_registered
        assert "config_only" not in fully_registered
        assert "services_only" not in fully_registered

    def test_get_registration_status(self):
        """Test getting registration status for a broker."""
        # Test nonexistent broker
        status = self.registry.get_registration_status("nonexistent")
        assert not status["config_registered"]
        assert not status["services_registered"]
        assert not status["fully_registered"]

        # Test config only
        self.registry.register_broker_config("config_only", MockConfig)
        status = self.registry.get_registration_status("config_only")
        assert status["config_registered"]
        assert not status["services_registered"]
        assert not status["fully_registered"]

        # Test complete registration
        services = {
            "portfolio": MockPortfolioService,
            "transaction": MockTransactionService,
            "deposit": MockDepositService,
        }
        self.registry.register_complete_broker("complete", MockConfig, **services)
        status = self.registry.get_registration_status("complete")
        assert status["config_registered"]
        assert status["services_registered"]
        assert status["fully_registered"]

    def test_validate_all_registrations(self):
        """Test validation of all registrations."""
        # Register config only
        self.registry.register_broker_config("config_only", MockConfig)

        # Register services only
        services = {
            "portfolio": MockPortfolioService,
            "transaction": MockTransactionService,
            "deposit": MockDepositService,
        }
        self.registry.register_broker_services("services_only", **services)

        # Register complete broker
        self.registry.register_complete_broker("complete", MockConfig, **services)

        issues = self.registry.validate_all_registrations()

        assert "services_only" in issues["missing_configs"]
        assert "config_only" in issues["missing_services"]
        assert "config_only" in issues["incomplete_registrations"]
        assert "services_only" in issues["incomplete_registrations"]
        assert "complete" not in issues["missing_configs"]
        assert "complete" not in issues["missing_services"]
        assert "complete" not in issues["incomplete_registrations"]

    # Cleanup tests
    def test_unregister_broker(self):
        """Test unregistering a broker."""
        services = {
            "portfolio": MockPortfolioService,
            "transaction": MockTransactionService,
            "deposit": MockDepositService,
        }

        self.registry.register_complete_broker("test_broker", MockConfig, **services)
        assert self.registry.is_fully_registered("test_broker")

        self.registry.unregister_broker("test_broker")
        assert not self.registry.is_config_registered("test_broker")
        assert not self.registry.is_service_registered("test_broker")
        assert not self.registry.is_fully_registered("test_broker")

    def test_unregister_nonexistent_broker(self):
        """Test unregistering a nonexistent broker does not raise error."""
        # Should not raise any exception
        self.registry.unregister_broker("nonexistent")

    def test_clear_all_registrations(self):
        """Test clearing all registrations."""
        # Clear any existing registrations from test setup
        self.registry.clear_all_registrations()

        services = {
            "portfolio": MockPortfolioService,
            "transaction": MockTransactionService,
            "deposit": MockDepositService,
        }

        self.registry.register_complete_broker("broker1", MockConfig, **services)
        self.registry.register_complete_broker("broker2", MockConfig, **services)

        assert len(self.registry.get_fully_registered_brokers()) == 2

        self.registry.clear_all_registrations()

        assert len(self.registry.get_fully_registered_brokers()) == 0
        assert len(self.registry.get_registered_config_brokers()) == 0
        assert len(self.registry.get_registered_service_brokers()) == 0

    # Singleton tests
    def test_singleton_behavior(self):
        """Test that registry follows singleton pattern."""
        registry1 = UnifiedBrokerRegistry()
        registry2 = UnifiedBrokerRegistry()

        assert registry1 is registry2

        # Register something in one instance
        registry1.register_broker_config("test", MockConfig)

        # Should be available in the other instance
        assert registry2.is_config_registered("test")

    # Edge cases and error handling
    def test_case_sensitivity_in_service_names(self):
        """Test that service names are case insensitive."""
        services = {
            "PORTFOLIO": MockPortfolioService,
            "Transaction": MockTransactionService,
            "deposit": MockDepositService,
        }

        # Should work regardless of case
        self.registry.register_broker_services("test_broker", **services)

        assert self.registry.broker_supports_service("test_broker", ServiceType.PORTFOLIO)
        assert self.registry.broker_supports_service("test_broker", ServiceType.TRANSACTION)
        assert self.registry.broker_supports_service("test_broker", ServiceType.DEPOSIT)

    def test_get_broker_capabilities_nonexistent_returns_empty(self):
        """Test that getting capabilities for nonexistent broker returns empty list."""
        capabilities = self.registry.get_broker_capabilities("nonexistent")
        assert capabilities == []

    def test_valid_broker_names(self):
        """Test various valid broker name formats."""
        valid_names = ["test", "test_broker", "broker123", "test123_broker"]

        for name in valid_names:
            self.registry.register_broker_config(name, MockConfig)
            assert self.registry.is_config_registered(name)

        # Clean up for next test
        self.registry.clear_all_registrations()
