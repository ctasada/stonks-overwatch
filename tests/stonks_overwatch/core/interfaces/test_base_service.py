"""
Tests for the BaseService and DependencyInjectionMixin.

This module contains comprehensive tests for the dependency injection
functionality provided by the base service classes.
"""

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.base_credentials import BaseCredentials
from stonks_overwatch.core.interfaces.base_service import BaseService, DependencyInjectionMixin

from unittest.mock import patch


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


class MockConfig(BaseConfig):
    """Mock configuration for testing."""

    config_key = "mock"

    def __init__(self, credentials=None, enabled=True, base_currency="EUR"):
        super().__init__(credentials, enabled)
        self.base_currency = base_currency

    @property
    def get_credentials(self):
        return self.credentials

    @classmethod
    def from_dict(cls, data: dict) -> "MockConfig":
        """Create MockConfig from dictionary data."""
        enabled = data.get("enabled", True)
        base_currency = data.get("base_currency", "EUR")
        credentials_data = data.get("credentials")
        credentials = MockCredentials() if credentials_data else None
        return cls(credentials, enabled, base_currency)

    @classmethod
    def default(cls):
        return cls(MockCredentials(), True, "EUR")


# Test implementation classes
class MockServiceWithMixin(DependencyInjectionMixin):
    """Mock service using the mixin directly."""

    def __init__(self, config=None, custom_param="default"):
        super().__init__(config)
        self.custom_param = custom_param


class MockServiceWithBaseService(BaseService):
    """Mock service using BaseService."""

    def __init__(self, config=None, another_param=42):
        super().__init__(config)
        self.another_param = another_param


class MockServiceWithMultipleArgs(BaseService):
    """Mock service with multiple arguments."""

    def __init__(self, required_arg, config=None, optional_arg="optional"):
        self.required_arg = required_arg
        super().__init__(config)
        self.optional_arg = optional_arg


class TestDependencyInjectionMixin:
    """Test cases for DependencyInjectionMixin."""

    def test_mixin_with_injected_config(self):
        """Test mixin with injected configuration."""
        config = MockConfig(base_currency="GBP")
        service = MockServiceWithMixin(config=config)

        assert service.config is config
        assert service.base_currency == "GBP"
        assert service.is_dependency_injection_enabled() is True

    @patch("stonks_overwatch.config.config.Config.get_global")
    def test_mixin_without_injected_config(self, mock_get_global):
        """Test mixin falls back to global config when no config injected."""
        mock_config = MockConfig(base_currency="USD")
        mock_get_global.return_value = mock_config

        service = MockServiceWithMixin()

        assert service.config is mock_config
        assert service.base_currency == "USD"
        assert service.is_dependency_injection_enabled() is False
        mock_get_global.assert_called_once()

    @patch("stonks_overwatch.config.config.Config.get_global")
    def test_mixin_global_config_caching(self, mock_get_global):
        """Test that global config is cached to avoid multiple calls."""
        mock_config = MockConfig()
        mock_get_global.return_value = mock_config

        service = MockServiceWithMixin()

        # Access config multiple times
        config1 = service.config
        config2 = service.config

        assert config1 is config2
        mock_get_global.assert_called_once()  # Should only be called once

    def test_mixin_with_config_having_base_currency(self):
        """Test mixin with config that has base_currency attribute."""
        config = MockConfig(base_currency="JPY")
        service = MockServiceWithMixin(config=config)

        assert service.base_currency == "JPY"

    def test_mixin_with_config_without_base_currency(self):
        """Test mixin with config that doesn't have base_currency attribute."""
        # Create a config without base_currency attribute
        config = MockConfig()
        delattr(config, "base_currency")

        with patch("stonks_overwatch.config.config.Config.get_global") as mock_get_global:
            mock_config = MockConfig(base_currency="CHF")
            mock_get_global.return_value = mock_config

            service = MockServiceWithMixin(config=config)

            # Should fall back to global config for base_currency
            assert service.base_currency == "CHF"

    def test_mixin_custom_parameters_preserved(self):
        """Test that custom parameters are preserved during initialization."""
        config = MockConfig()
        service = MockServiceWithMixin(config=config, custom_param="custom_value")

        assert service.config is config
        assert service.custom_param == "custom_value"


class TestBaseService:
    """Test cases for BaseService."""

    def test_base_service_with_injected_config(self):
        """Test BaseService with injected configuration."""
        config = MockConfig(base_currency="CAD")
        service = MockServiceWithBaseService(config=config)

        assert service.config is config
        assert service.base_currency == "CAD"
        assert service.is_dependency_injection_enabled() is True

    @patch("stonks_overwatch.config.config.Config.get_global")
    def test_base_service_without_injected_config(self, mock_get_global):
        """Test BaseService falls back to global config."""
        mock_config = MockConfig(base_currency="AUD")
        mock_get_global.return_value = mock_config

        service = MockServiceWithBaseService()

        assert service.config is mock_config
        assert service.base_currency == "AUD"
        assert service.is_dependency_injection_enabled() is False

    def test_base_service_custom_parameters(self):
        """Test BaseService preserves custom parameters."""
        config = MockConfig()
        service = MockServiceWithBaseService(config=config, another_param=100)

        assert service.config is config
        assert service.another_param == 100

    def test_base_service_multiple_args(self):
        """Test BaseService with multiple arguments."""
        config = MockConfig()
        service = MockServiceWithMultipleArgs("required", config=config, optional_arg="custom")

        assert service.required_arg == "required"
        assert service.config is config
        assert service.optional_arg == "custom"

    @patch("stonks_overwatch.config.config.Config.get_global")
    def test_base_service_multiple_args_no_config(self, mock_get_global):
        """Test BaseService with multiple arguments but no injected config."""
        mock_config = MockConfig()
        mock_get_global.return_value = mock_config

        service = MockServiceWithMultipleArgs("required")

        assert service.required_arg == "required"
        assert service.config is mock_config
        assert service.optional_arg == "optional"


class TestBackwardCompatibility:
    """Test cases for backward compatibility."""

    @patch("stonks_overwatch.config.config.Config.get_global")
    def test_existing_service_still_works(self, mock_get_global):
        """Test that services without dependency injection still work."""
        mock_config = MockConfig(base_currency="SEK")
        mock_get_global.return_value = mock_config

        # Simulate existing service that doesn't use dependency injection
        service = MockServiceWithBaseService()

        # Should work exactly as before
        assert service.base_currency == "SEK"
        assert service.is_dependency_injection_enabled() is False

    def test_config_priority(self):
        """Test configuration priority: injected > global."""
        injected_config = MockConfig(base_currency="NOK")

        with patch("stonks_overwatch.config.config.Config.get_global") as mock_get_global:
            mock_config = MockConfig(base_currency="DKK")
            mock_get_global.return_value = mock_config

            service = MockServiceWithBaseService(config=injected_config)

            # Should use injected config, not global
            assert service.base_currency == "NOK"
            # Global config should not be accessed when injected config is provided
            mock_get_global.assert_not_called()


class TestEdgeCases:
    """Test cases for edge cases and error scenarios."""

    def test_none_config_injection(self):
        """Test explicitly passing None as config."""
        with patch("stonks_overwatch.config.config.Config.get_global") as mock_get_global:
            mock_config = MockConfig()
            mock_get_global.return_value = mock_config

            service = MockServiceWithBaseService(config=None)

            # Should fall back to global config
            assert service.config is mock_config
            assert service.is_dependency_injection_enabled() is False

    def test_config_with_none_base_currency(self):
        """Test config with None base_currency."""
        config = MockConfig()
        config.base_currency = None

        with patch("stonks_overwatch.config.config.Config.get_global") as mock_get_global:
            mock_config = MockConfig(base_currency="DEFAULT")
            mock_get_global.return_value = mock_config

            service = MockServiceWithBaseService(config=config)

            # Should fall back to global config for base_currency
            assert service.base_currency == "DEFAULT"

    def test_empty_string_base_currency(self):
        """Test config with empty string base_currency."""
        config = MockConfig(base_currency="")
        service = MockServiceWithBaseService(config=config)

        # Should return empty string as specified
        assert service.base_currency == ""

    def test_multiple_service_instances_independence(self):
        """Test that multiple service instances are independent."""
        config1 = MockConfig(base_currency="EUR")
        config2 = MockConfig(base_currency="USD")

        service1 = MockServiceWithBaseService(config=config1)
        service2 = MockServiceWithBaseService(config=config2)

        assert service1.config is config1
        assert service2.config is config2
        assert service1.base_currency == "EUR"
        assert service2.base_currency == "USD"
        assert service1.is_dependency_injection_enabled() is True
        assert service2.is_dependency_injection_enabled() is True
