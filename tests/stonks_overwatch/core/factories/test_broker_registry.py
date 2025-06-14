"""
Tests for BrokerRegistry.

This module contains comprehensive tests for the broker service registry,
covering registration, capabilities management, and service lookup.
"""

from stonks_overwatch.core.exceptions import ServiceRegistryException
from stonks_overwatch.core.factories.broker_registry import BrokerRegistry, ServiceType
from stonks_overwatch.core.interfaces.deposit_service import DepositServiceInterface
from stonks_overwatch.core.interfaces.dividend_service import DividendServiceInterface
from stonks_overwatch.core.interfaces.portfolio_service import PortfolioServiceInterface
from stonks_overwatch.core.interfaces.transaction_service import TransactionServiceInterface

import pytest
from unittest.mock import MagicMock


class TestBrokerRegistry:
    """Test cases for BrokerRegistry."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Clear singleton instance for clean state
        if hasattr(BrokerRegistry, "_instance"):
            BrokerRegistry._instance = None

        self.registry = BrokerRegistry()

        # Create mock service classes
        self.mock_portfolio_service = MagicMock(spec=PortfolioServiceInterface)
        self.mock_transaction_service = MagicMock(spec=TransactionServiceInterface)
        self.mock_deposit_service = MagicMock(spec=DepositServiceInterface)
        self.mock_dividend_service = MagicMock(spec=DividendServiceInterface)
        self.mock_fee_service = MagicMock()
        self.mock_account_service = MagicMock()

    def teardown_method(self):
        """Clean up after each test method."""
        # Clear registry state
        self.registry._brokers.clear()
        self.registry._broker_capabilities.clear()

        # Clear singleton instance
        if hasattr(BrokerRegistry, "_instance"):
            BrokerRegistry._instance = None

    def test_singleton_behavior(self):
        """Test that BrokerRegistry is a singleton."""
        registry1 = BrokerRegistry()
        registry2 = BrokerRegistry()

        assert registry1 is registry2
        assert id(registry1) == id(registry2)

    def test_register_broker_with_required_services(self):
        """Test registering a broker with only required services."""
        self.registry.register_broker(
            broker_name="test_broker",
            portfolio_service=self.mock_portfolio_service,
            transaction_service=self.mock_transaction_service,
            deposit_service=self.mock_deposit_service,
        )

        # Check broker is registered
        assert "test_broker" in self.registry.get_available_brokers()

        # Check required services are available
        assert self.registry.get_broker_service("test_broker", ServiceType.PORTFOLIO) == self.mock_portfolio_service
        assert self.registry.get_broker_service("test_broker", ServiceType.TRANSACTION) == self.mock_transaction_service
        assert self.registry.get_broker_service("test_broker", ServiceType.DEPOSIT) == self.mock_deposit_service

        # Check capabilities include required services
        capabilities = self.registry.get_broker_capabilities("test_broker")
        assert ServiceType.PORTFOLIO in capabilities
        assert ServiceType.TRANSACTION in capabilities
        assert ServiceType.DEPOSIT in capabilities
        assert len(capabilities) == 3

    def test_register_broker_with_all_services(self):
        """Test registering a broker with all services."""
        self.registry.register_broker(
            broker_name="full_broker",
            portfolio_service=self.mock_portfolio_service,
            transaction_service=self.mock_transaction_service,
            deposit_service=self.mock_deposit_service,
            dividend_service=self.mock_dividend_service,
            fee_service=self.mock_fee_service,
            account_service=self.mock_account_service,
        )

        # Check all services are available
        assert self.registry.get_broker_service("full_broker", ServiceType.PORTFOLIO) == self.mock_portfolio_service
        assert self.registry.get_broker_service("full_broker", ServiceType.TRANSACTION) == self.mock_transaction_service
        assert self.registry.get_broker_service("full_broker", ServiceType.DEPOSIT) == self.mock_deposit_service
        assert self.registry.get_broker_service("full_broker", ServiceType.DIVIDEND) == self.mock_dividend_service
        assert self.registry.get_broker_service("full_broker", ServiceType.FEE) == self.mock_fee_service
        assert self.registry.get_broker_service("full_broker", ServiceType.ACCOUNT) == self.mock_account_service

        # Check capabilities include all services
        capabilities = self.registry.get_broker_capabilities("full_broker")
        assert len(capabilities) == 6
        assert all(service_type in capabilities for service_type in ServiceType)

    def test_register_duplicate_broker_raises_exception(self):
        """Test that registering a duplicate broker raises an exception."""
        # Register broker first time
        self.registry.register_broker(
            broker_name="duplicate_broker",
            portfolio_service=self.mock_portfolio_service,
            transaction_service=self.mock_transaction_service,
            deposit_service=self.mock_deposit_service,
        )

        # Try to register same broker again
        with pytest.raises(ServiceRegistryException) as exc_info:
            self.registry.register_broker(
                broker_name="duplicate_broker",
                portfolio_service=self.mock_portfolio_service,
                transaction_service=self.mock_transaction_service,
                deposit_service=self.mock_deposit_service,
            )

        assert "Broker 'duplicate_broker' is already registered" in str(exc_info.value)

    def test_get_broker_service_nonexistent_broker(self):
        """Test getting service from non-existent broker returns None."""
        result = self.registry.get_broker_service("nonexistent", ServiceType.PORTFOLIO)
        assert result is None

    def test_get_broker_service_unsupported_service(self):
        """Test getting unsupported service returns None."""
        # Register broker without dividend service
        self.registry.register_broker(
            broker_name="limited_broker",
            portfolio_service=self.mock_portfolio_service,
            transaction_service=self.mock_transaction_service,
            deposit_service=self.mock_deposit_service,
        )

        result = self.registry.get_broker_service("limited_broker", ServiceType.DIVIDEND)
        assert result is None

    def test_get_available_brokers_empty(self):
        """Test getting available brokers when none are registered."""
        brokers = self.registry.get_available_brokers()
        assert brokers == []

    def test_get_available_brokers_with_registrations(self):
        """Test getting available brokers after registrations."""
        # Register two brokers
        self.registry.register_broker(
            broker_name="broker1",
            portfolio_service=self.mock_portfolio_service,
            transaction_service=self.mock_transaction_service,
            deposit_service=self.mock_deposit_service,
        )

        self.registry.register_broker(
            broker_name="broker2",
            portfolio_service=self.mock_portfolio_service,
            transaction_service=self.mock_transaction_service,
            deposit_service=self.mock_deposit_service,
        )

        brokers = self.registry.get_available_brokers()
        assert len(brokers) == 2
        assert "broker1" in brokers
        assert "broker2" in brokers

    def test_get_broker_capabilities_nonexistent_broker(self):
        """Test getting capabilities for non-existent broker."""
        capabilities = self.registry.get_broker_capabilities("nonexistent")
        assert capabilities == []

    def test_broker_supports_service_supported(self):
        """Test checking if broker supports a service it has."""
        self.registry.register_broker(
            broker_name="test_broker",
            portfolio_service=self.mock_portfolio_service,
            transaction_service=self.mock_transaction_service,
            deposit_service=self.mock_deposit_service,
            dividend_service=self.mock_dividend_service,
        )

        assert self.registry.broker_supports_service("test_broker", ServiceType.PORTFOLIO) is True
        assert self.registry.broker_supports_service("test_broker", ServiceType.DIVIDEND) is True

    def test_broker_supports_service_unsupported(self):
        """Test checking if broker supports a service it doesn't have."""
        # Register broker without fee service
        self.registry.register_broker(
            broker_name="test_broker",
            portfolio_service=self.mock_portfolio_service,
            transaction_service=self.mock_transaction_service,
            deposit_service=self.mock_deposit_service,
        )

        assert self.registry.broker_supports_service("test_broker", ServiceType.FEE) is False

    def test_broker_supports_service_nonexistent_broker(self):
        """Test checking if non-existent broker supports a service."""
        assert self.registry.broker_supports_service("nonexistent", ServiceType.PORTFOLIO) is False

    def test_unregister_broker(self):
        """Test unregistering a broker."""
        # Register broker
        self.registry.register_broker(
            broker_name="test_broker",
            portfolio_service=self.mock_portfolio_service,
            transaction_service=self.mock_transaction_service,
            deposit_service=self.mock_deposit_service,
        )

        # Verify broker is registered
        assert "test_broker" in self.registry.get_available_brokers()
        assert self.registry.broker_supports_service("test_broker", ServiceType.PORTFOLIO) is True

        # Unregister broker
        self.registry.unregister_broker("test_broker")

        # Verify broker is no longer available
        assert "test_broker" not in self.registry.get_available_brokers()
        assert self.registry.broker_supports_service("test_broker", ServiceType.PORTFOLIO) is False
        assert self.registry.get_broker_service("test_broker", ServiceType.PORTFOLIO) is None

    def test_unregister_nonexistent_broker(self):
        """Test unregistering a non-existent broker (should not raise exception)."""
        # Should not raise exception
        self.registry.unregister_broker("nonexistent")

        # Registry should still be empty
        assert self.registry.get_available_brokers() == []

    def test_service_type_enum_values(self):
        """Test that ServiceType enum has expected values."""
        expected_values = ["portfolio", "transaction", "deposit", "dividend", "fee", "account"]
        actual_values = [service_type.value for service_type in ServiceType]

        assert len(actual_values) == len(expected_values)
        for expected in expected_values:
            assert expected in actual_values

    def test_multiple_brokers_independent_capabilities(self):
        """Test that multiple brokers can have different capabilities."""
        # Register broker with basic services
        self.registry.register_broker(
            broker_name="basic_broker",
            portfolio_service=self.mock_portfolio_service,
            transaction_service=self.mock_transaction_service,
            deposit_service=self.mock_deposit_service,
        )

        # Register broker with extended services
        self.registry.register_broker(
            broker_name="extended_broker",
            portfolio_service=self.mock_portfolio_service,
            transaction_service=self.mock_transaction_service,
            deposit_service=self.mock_deposit_service,
            dividend_service=self.mock_dividend_service,
            fee_service=self.mock_fee_service,
        )

        # Check capabilities are independent
        basic_capabilities = self.registry.get_broker_capabilities("basic_broker")
        extended_capabilities = self.registry.get_broker_capabilities("extended_broker")

        assert len(basic_capabilities) == 3
        assert len(extended_capabilities) == 5

        assert self.registry.broker_supports_service("basic_broker", ServiceType.DIVIDEND) is False
        assert self.registry.broker_supports_service("extended_broker", ServiceType.DIVIDEND) is True
