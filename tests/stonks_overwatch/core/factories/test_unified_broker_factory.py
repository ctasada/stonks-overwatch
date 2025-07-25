"""
Tests for the UnifiedBrokerFactory.

This module contains comprehensive tests for the unified broker factory
functionality, including configuration creation, service creation with
dependency injection, caching, and error handling.
"""

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.base_credentials import BaseCredentials
from stonks_overwatch.core.factories.broker_registry import ServiceType
from stonks_overwatch.core.factories.unified_broker_factory import (
    UnifiedBrokerFactory,
    UnifiedBrokerFactoryError,
)
from stonks_overwatch.core.factories.unified_broker_registry import (
    UnifiedBrokerRegistry,
)

import pytest


# Test fixtures (reuse from registry tests)
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


class MockConfigWithError(BaseConfig):
    """Mock configuration that raises errors for testing."""

    config_key = "mock_error"

    def __init__(self, credentials=None, enabled=True):
        raise ValueError("Test error in config creation")

    @property
    def get_credentials(self):
        return None

    @classmethod
    def default(cls):
        raise ValueError("Test error in default config creation")

    @classmethod
    def from_dict(cls, data):
        raise ValueError("Test error in from_dict config creation")


class MockPortfolioService:
    """Mock portfolio service for testing (not inheriting from interface to avoid abstract methods)."""

    def __init__(self, config=None, **kwargs):
        self.config = config
        self.kwargs = kwargs


class MockTransactionService:
    """Mock transaction service for testing (not inheriting from interface to avoid abstract methods)."""

    def __init__(self, config=None, **kwargs):
        self.config = config
        self.kwargs = kwargs


class MockDepositService:
    """Mock deposit service for testing (not inheriting from interface to avoid abstract methods)."""

    def __init__(self, config=None, **kwargs):
        self.config = config
        self.kwargs = kwargs


class MockServiceWithError:
    """Mock service that raises errors for testing."""

    def __init__(self, config=None, **kwargs):
        raise ValueError("Test error in service creation")


class TestUnifiedBrokerFactory:
    """Test cases for UnifiedBrokerFactory."""

    def setup_method(self):
        """Set up test fixtures."""
        # Clear singleton state before each test
        if hasattr(UnifiedBrokerFactory, "_instances"):
            UnifiedBrokerFactory._instances.clear()
        if hasattr(UnifiedBrokerRegistry, "_instances"):
            UnifiedBrokerRegistry._instances.clear()

        self.factory = UnifiedBrokerFactory()
        self.registry = self.factory._registry

        # Ensure caching is enabled for each test
        self.factory.enable_caching()

        # Set up test broker with config and services
        self.registry.register_broker_config("test_broker", MockConfig)
        services = {
            "portfolio": MockPortfolioService,
            "transaction": MockTransactionService,
            "deposit": MockDepositService,
        }
        self.registry.register_broker_services("test_broker", **services)

    def teardown_method(self):
        """Clean up after each test."""
        self.registry.clear_all_registrations()
        self.factory.clear_cache()

    # Configuration creation tests
    def test_create_config_success(self):
        """Test successful configuration creation."""
        config = self.factory.create_config("test_broker")

        assert config is not None
        assert isinstance(config, MockConfig)
        assert config.is_enabled()

    def test_create_config_with_kwargs(self):
        """Test configuration creation with custom arguments."""
        config = self.factory.create_config("test_broker", enabled=False)

        assert config is not None
        assert isinstance(config, MockConfig)
        assert not config.is_enabled()

    def test_create_config_caching(self):
        """Test that configuration instances are cached."""
        # Ensure cache is enabled
        assert self.factory._cache_enabled == True

        config1 = self.factory.create_config("test_broker")

        # Check that it was cached
        assert "test_broker" in self.factory._config_instances
        assert self.factory._config_instances["test_broker"] is config1

        config2 = self.factory.create_config("test_broker")

        assert config1 is config2  # Same instance due to caching

    def test_create_config_no_caching(self):
        """Test configuration creation with caching disabled."""
        self.factory.disable_caching()

        config1 = self.factory.create_config("test_broker")
        config2 = self.factory.create_config("test_broker")

        assert config1 is not config2  # Different instances

    def test_create_config_nonexistent_broker(self):
        """Test configuration creation for nonexistent broker."""
        config = self.factory.create_config("nonexistent")
        assert config is None

    def test_create_config_error_handling(self):
        """Test configuration creation error handling."""
        self.registry.register_broker_config("error_broker", MockConfigWithError)

        with pytest.raises(UnifiedBrokerFactoryError, match="Failed to create configuration"):
            self.factory.create_config("error_broker")

    def test_create_default_config_success(self):
        """Test successful default configuration creation."""
        config = self.factory.create_default_config("test_broker")

        assert config is not None
        assert isinstance(config, MockConfig)
        assert config.is_enabled()

    def test_create_default_config_error_handling(self):
        """Test default configuration creation error handling."""
        self.registry.register_broker_config("error_broker", MockConfigWithError)

        with pytest.raises(UnifiedBrokerFactoryError, match="Failed to create default configuration"):
            self.factory.create_default_config("error_broker")

    def test_create_config_from_dict_success(self):
        """Test successful configuration creation from dictionary."""
        config = self.factory.create_config_from_dict("test_broker", {"enabled": True})

        assert config is not None
        assert isinstance(config, MockConfig)

    def test_create_config_from_dict_error_handling(self):
        """Test configuration from dict creation error handling."""
        self.registry.register_broker_config("error_broker", MockConfigWithError)

        with pytest.raises(UnifiedBrokerFactoryError, match="Failed to create configuration from dict"):
            self.factory.create_config_from_dict("error_broker", {})

    # Service creation tests
    def test_create_service_success(self):
        """Test successful service creation."""
        service = self.factory.create_service("test_broker", ServiceType.PORTFOLIO)

        assert service is not None
        assert isinstance(service, MockPortfolioService)

    def test_create_service_with_dependency_injection(self):
        """Test that configuration is automatically injected into services."""
        service = self.factory.create_service("test_broker", ServiceType.PORTFOLIO)

        assert service.config is not None
        assert isinstance(service.config, MockConfig)

    def test_create_service_with_explicit_config(self):
        """Test service creation with explicitly provided config."""
        explicit_config = MockConfig(enabled=False)
        service = self.factory.create_service("test_broker", ServiceType.PORTFOLIO, config=explicit_config)

        assert service.config is explicit_config
        assert not service.config.is_enabled()

    def test_create_service_with_additional_kwargs(self):
        """Test service creation with additional arguments."""
        service = self.factory.create_service("test_broker", ServiceType.PORTFOLIO, extra_arg="test")

        assert service.kwargs["extra_arg"] == "test"

    def test_create_service_caching(self):
        """Test that service instances are cached."""
        # Ensure cache is enabled
        assert self.factory._cache_enabled == True

        service1 = self.factory.create_service("test_broker", ServiceType.PORTFOLIO)

        # Check that it was cached
        assert "test_broker" in self.factory._service_instances
        assert ServiceType.PORTFOLIO in self.factory._service_instances["test_broker"]
        assert self.factory._service_instances["test_broker"][ServiceType.PORTFOLIO] is service1

        service2 = self.factory.create_service("test_broker", ServiceType.PORTFOLIO)

        assert service1 is service2  # Same instance due to caching

    def test_create_service_different_types_cached_separately(self):
        """Test that different service types are cached separately."""
        portfolio_service = self.factory.create_service("test_broker", ServiceType.PORTFOLIO)
        transaction_service = self.factory.create_service("test_broker", ServiceType.TRANSACTION)

        assert portfolio_service is not transaction_service
        assert isinstance(portfolio_service, MockPortfolioService)
        assert isinstance(transaction_service, MockTransactionService)

    def test_create_service_nonexistent_broker(self):
        """Test service creation for nonexistent broker."""
        service = self.factory.create_service("nonexistent", ServiceType.PORTFOLIO)
        assert service is None

    def test_create_service_unsupported_service_type(self):
        """Test service creation for unsupported service type."""
        service = self.factory.create_service("test_broker", ServiceType.DIVIDEND)
        assert service is None

    def test_create_service_error_handling(self):
        """Test service creation error handling."""
        # Register config and all required services (with one error service)
        self.registry.register_broker_config("error_broker", MockConfig)
        self.registry.register_broker_services(
            "error_broker",
            portfolio=MockServiceWithError,
            transaction=MockTransactionService,
            deposit=MockDepositService,
        )

        with pytest.raises(UnifiedBrokerFactoryError, match="Failed to create portfolio service"):
            self.factory.create_service("error_broker", ServiceType.PORTFOLIO)

    # Typed service creation tests
    def test_create_portfolio_service_success(self):
        """Test successful portfolio service creation."""
        service = self.factory.create_portfolio_service("test_broker")

        assert service is not None
        assert isinstance(service, MockPortfolioService)

    def test_create_portfolio_service_unsupported(self):
        """Test portfolio service creation for unsupported broker."""
        # Register config only, no services
        self.registry.register_broker_config("minimal_broker", MockConfig)

        # Try to create portfolio service without registering any services
        with pytest.raises(UnifiedBrokerFactoryError, match="does not support portfolio service"):
            self.factory.create_portfolio_service("minimal_broker")

    def test_create_transaction_service_success(self):
        """Test successful transaction service creation."""
        service = self.factory.create_transaction_service("test_broker")

        assert service is not None
        assert isinstance(service, MockTransactionService)

    def test_create_deposit_service_success(self):
        """Test successful deposit service creation."""
        service = self.factory.create_deposit_service("test_broker")

        assert service is not None
        assert isinstance(service, MockDepositService)

    def test_create_dividend_service_unsupported_returns_none(self):
        """Test that creating unsupported dividend service returns None."""
        service = self.factory.create_dividend_service("test_broker")
        assert service is None

    def test_create_fee_service_unsupported_returns_none(self):
        """Test that creating unsupported fee service returns None."""
        service = self.factory.create_fee_service("test_broker")
        assert service is None

    def test_create_account_service_unsupported_returns_none(self):
        """Test that creating unsupported account service returns None."""
        service = self.factory.create_account_service("test_broker")
        assert service is None

    # Convenience methods tests
    def test_create_all_services(self):
        """Test creating all supported services for a broker."""
        services = self.factory.create_all_services("test_broker")

        assert len(services) == 3
        assert ServiceType.PORTFOLIO in services
        assert ServiceType.TRANSACTION in services
        assert ServiceType.DEPOSIT in services
        assert isinstance(services[ServiceType.PORTFOLIO], MockPortfolioService)

    def test_create_all_services_with_errors(self):
        """Test that create_all_services handles individual service errors gracefully."""
        # Register a broker with one working service and one error service
        self.registry.register_broker_config("mixed_broker", MockConfig)
        self.registry.register_broker_services(
            "mixed_broker", portfolio=MockPortfolioService, transaction=MockServiceWithError, deposit=MockDepositService
        )

        services = self.factory.create_all_services("mixed_broker")

        # Should have 2 services (portfolio and deposit), transaction should fail silently
        assert len(services) == 2
        assert ServiceType.PORTFOLIO in services
        assert ServiceType.DEPOSIT in services
        assert ServiceType.TRANSACTION not in services

    def test_get_available_brokers(self):
        """Test getting available brokers."""
        brokers = self.factory.get_available_brokers()
        assert "test_broker" in brokers

    def test_is_broker_available(self):
        """Test checking if broker is available."""
        assert self.factory.is_broker_available("test_broker")
        assert not self.factory.is_broker_available("nonexistent")

    def test_get_broker_capabilities(self):
        """Test getting broker capabilities."""
        capabilities = self.factory.get_broker_capabilities("test_broker")
        assert ServiceType.PORTFOLIO in capabilities
        assert ServiceType.TRANSACTION in capabilities
        assert ServiceType.DEPOSIT in capabilities

    def test_broker_supports_service(self):
        """Test checking if broker supports service."""
        assert self.factory.broker_supports_service("test_broker", ServiceType.PORTFOLIO)
        assert not self.factory.broker_supports_service("test_broker", ServiceType.DIVIDEND)

    # Cache management tests
    def test_clear_cache_specific_broker(self):
        """Test clearing cache for specific broker."""
        # Create instances for two brokers
        self.registry.register_complete_broker(
            "broker2",
            MockConfig,
            portfolio=MockPortfolioService,
            transaction=MockTransactionService,
            deposit=MockDepositService,
        )

        config1 = self.factory.create_config("test_broker")
        config2 = self.factory.create_config("broker2")

        # Clear cache for one broker
        self.factory.clear_cache("test_broker")

        # test_broker instances should be recreated, broker2 should be cached
        new_config1 = self.factory.create_config("test_broker")
        cached_config2 = self.factory.create_config("broker2")

        assert new_config1 is not config1  # Recreated
        assert cached_config2 is config2  # Still cached

    def test_clear_cache_all(self):
        """Test clearing all cache."""
        config = self.factory.create_config("test_broker")
        service = self.factory.create_service("test_broker", ServiceType.PORTFOLIO)

        self.factory.clear_cache()

        new_config = self.factory.create_config("test_broker")
        new_service = self.factory.create_service("test_broker", ServiceType.PORTFOLIO)

        assert new_config is not config
        assert new_service is not service

    def test_cache_enable_disable(self):
        """Test enabling and disabling cache."""
        # Test with cache enabled (default)
        config1 = self.factory.create_config("test_broker")
        config2 = self.factory.create_config("test_broker")
        assert config1 is config2

        # Disable cache
        self.factory.disable_caching()
        config3 = self.factory.create_config("test_broker")
        config4 = self.factory.create_config("test_broker")
        assert config3 is not config4

        # Re-enable cache
        self.factory.enable_caching()
        config5 = self.factory.create_config("test_broker")
        config6 = self.factory.create_config("test_broker")
        assert config5 is config6

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        # Create some instances
        self.factory.create_config("test_broker")
        self.factory.create_service("test_broker", ServiceType.PORTFOLIO)
        self.factory.create_service("test_broker", ServiceType.TRANSACTION)

        stats = self.factory.get_cache_stats()

        assert stats["cache_enabled"] is True
        assert "test_broker" in stats["cached_configs"]
        assert "test_broker" in stats["cached_services"]
        assert len(stats["cached_services"]["test_broker"]) == 2
        assert stats["total_config_instances"] == 1
        assert stats["total_service_instances"] == 2

    # Singleton tests
    def test_singleton_behavior(self):
        """Test that factory follows singleton pattern."""
        factory1 = UnifiedBrokerFactory()
        factory2 = UnifiedBrokerFactory()

        assert factory1 is factory2

        # Create config in one instance
        config1 = factory1.create_config("test_broker")

        # Should be available (cached) in the other instance
        config2 = factory2.create_config("test_broker")
        assert config1 is config2

    # Integration tests
    def test_full_workflow_integration(self):
        """Test full workflow from registration to service creation."""
        # Register complete broker
        self.registry.register_complete_broker(
            "integration_broker",
            MockConfig,
            portfolio=MockPortfolioService,
            transaction=MockTransactionService,
            deposit=MockDepositService,
        )

        # Create configuration
        config = self.factory.create_default_config("integration_broker")
        assert config is not None

        # Create services with dependency injection
        portfolio_service = self.factory.create_portfolio_service("integration_broker")
        assert portfolio_service is not None
        assert portfolio_service.config is not None

        # Verify all services work
        all_services = self.factory.create_all_services("integration_broker")
        assert len(all_services) == 3

        # Verify capabilities
        assert self.factory.is_broker_available("integration_broker")
        capabilities = self.factory.get_broker_capabilities("integration_broker")
        assert len(capabilities) == 3
