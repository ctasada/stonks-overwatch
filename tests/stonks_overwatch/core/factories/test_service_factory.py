"""
Tests for ServiceFactory.

This module contains comprehensive tests for the service factory,
covering service creation, caching, dependency injection, and error handling.
"""

from stonks_overwatch.core.exceptions import ServiceFactoryException
from stonks_overwatch.core.factories.broker_registry import BrokerRegistry
from stonks_overwatch.core.factories.service_factory import ServiceFactory
from stonks_overwatch.core.interfaces.deposit_service import DepositServiceInterface
from stonks_overwatch.core.interfaces.portfolio_service import PortfolioServiceInterface
from stonks_overwatch.core.interfaces.transaction_service import TransactionServiceInterface

import pytest
from unittest.mock import MagicMock

class TestServiceFactory:
    """Test cases for ServiceFactory."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Clear singleton instances for clean state
        if hasattr(ServiceFactory, '_instance'):
            ServiceFactory._instance = None
        if hasattr(BrokerRegistry, '_instance'):
            BrokerRegistry._instance = None

        self.factory = ServiceFactory()
        self.registry = BrokerRegistry()

        # Create mock service classes that can be instantiated
        self.mock_portfolio_service_class = MagicMock()
        self.mock_portfolio_service_instance = MagicMock(spec=PortfolioServiceInterface)
        self.mock_portfolio_service_class.return_value = self.mock_portfolio_service_instance

        self.mock_transaction_service_class = MagicMock()
        self.mock_transaction_service_instance = MagicMock(spec=TransactionServiceInterface)
        self.mock_transaction_service_class.return_value = self.mock_transaction_service_instance

        self.mock_deposit_service_class = MagicMock()
        self.mock_deposit_service_instance = MagicMock(spec=DepositServiceInterface)
        self.mock_deposit_service_class.return_value = self.mock_deposit_service_instance

    def teardown_method(self):
        """Clean up after each test method."""
        # Clear registry state
        self.registry._brokers.clear()
        self.registry._broker_capabilities.clear()

        # Clear factory cache
        self.factory.clear_cache()

        # Clear singleton instances
        if hasattr(ServiceFactory, '_instance'):
            ServiceFactory._instance = None
        if hasattr(BrokerRegistry, '_instance'):
            BrokerRegistry._instance = None

    def test_singleton_behavior(self):
        """Test that ServiceFactory is a singleton."""
        factory1 = ServiceFactory()
        factory2 = ServiceFactory()

        assert factory1 is factory2

    def test_create_portfolio_service_success(self):
        """Test successful creation of portfolio service."""
        # Register broker
        self.registry.register_broker(
            broker_name="test_broker",
            portfolio_service=self.mock_portfolio_service_class,
            transaction_service=self.mock_transaction_service_class,
            deposit_service=self.mock_deposit_service_class
        )

        # Create service
        service = self.factory.create_portfolio_service("test_broker")

        # Verify service creation
        assert service == self.mock_portfolio_service_instance
        self.mock_portfolio_service_class.assert_called_once_with()

    def test_create_portfolio_service_unsupported_broker(self):
        """Test creating portfolio service for unsupported broker."""
        with pytest.raises(ServiceFactoryException) as exc_info:
            self.factory.create_portfolio_service("nonexistent_broker")

        assert "Broker 'nonexistent_broker' does not support portfolio service" in str(exc_info.value)

    def test_service_caching(self):
        """Test that services are cached and reused."""
        # Register broker
        self.registry.register_broker(
            broker_name="test_broker",
            portfolio_service=self.mock_portfolio_service_class,
            transaction_service=self.mock_transaction_service_class,
            deposit_service=self.mock_deposit_service_class
        )

        # Create service twice
        service1 = self.factory.create_portfolio_service("test_broker")
        service2 = self.factory.create_portfolio_service("test_broker")

        # Verify same instance is returned and class is called only once
        assert service1 is service2
        self.mock_portfolio_service_class.assert_called_once_with()

    def test_clear_cache_all(self):
        """Test clearing cache for all brokers."""
        # Register broker and create service
        self.registry.register_broker(
            broker_name="test_broker",
            portfolio_service=self.mock_portfolio_service_class,
            transaction_service=self.mock_transaction_service_class,
            deposit_service=self.mock_deposit_service_class
        )

        # Create service (should be cached)
        self.factory.create_portfolio_service("test_broker")

        # Clear all cache
        self.factory.clear_cache()

        # Create service again (should create new instance)
        self.factory.create_portfolio_service("test_broker")

        # Verify class was called twice (new instance created)
        assert self.mock_portfolio_service_class.call_count == 2
