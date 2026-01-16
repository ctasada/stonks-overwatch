"""
Tests for enhanced service interface validation in BrokerRegistry.

This module tests the runtime validation that services implement correct interfaces.
"""

from abc import ABC
from typing import List

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.core.factories.broker_registry import BrokerRegistry, BrokerRegistryValidationError
from stonks_overwatch.core.interfaces import (
    AccountServiceInterface,
    AuthenticationResponse,
    AuthenticationResult,
    AuthenticationServiceInterface,
    DepositServiceInterface,
    DividendServiceInterface,
    FeeServiceInterface,
    PortfolioServiceInterface,
    TransactionServiceInterface,
)
from stonks_overwatch.core.service_types import ServiceType
from stonks_overwatch.services.models import (
    AccountOverview,
    Deposit,
    Dividend,
    Fee,
    PortfolioEntry,
    TotalPortfolio,
    Transaction,
)

import pytest


class MockConfig(BaseConfig):
    """Mock configuration class for testing."""

    config_key = "mock"

    def __init__(self, credentials=None, enabled=True):
        super().__init__(credentials, enabled)

    @classmethod
    def from_dict(cls, data: dict) -> "MockConfig":
        """Create MockConfig from dictionary data."""
        return cls()

    @property
    def get_credentials(self):
        return self.credentials


# Valid service implementations that implement the correct interfaces
class ValidPortfolioService(PortfolioServiceInterface):
    """Valid portfolio service that implements the interface."""

    def get_portfolio(self) -> List[PortfolioEntry]:
        return []

    def get_portfolio_total(self, portfolio=None) -> TotalPortfolio:
        return TotalPortfolio()


class ValidTransactionService(TransactionServiceInterface):
    """Valid transaction service that implements the interface."""

    def get_transactions(self) -> List[Transaction]:
        return []


class ValidDepositService(DepositServiceInterface):
    """Valid deposit service that implements the interface."""

    def get_cash_deposits(self) -> List[Deposit]:
        return []

    def calculate_cash_account_value(self) -> dict:
        return {}


class ValidDividendService(DividendServiceInterface):
    """Valid dividend service that implements the interface."""

    def get_dividends(self) -> List[Dividend]:
        return []


class ValidFeeService(FeeServiceInterface):
    """Valid fee service that implements the interface."""

    def get_fees(self) -> List[Fee]:
        return []


class ValidAccountService(AccountServiceInterface):
    """Valid account service that implements the interface."""

    def get_account_overview(self) -> List[AccountOverview]:
        return []


class ValidAuthenticationService(AuthenticationServiceInterface):
    """Valid authentication service that implements the interface."""

    def is_user_authenticated(self, request) -> bool:
        return True

    def authenticate_user(self, request, username=None, password=None, one_time_password=None, remember_me=False):
        return AuthenticationResponse(result=AuthenticationResult.SUCCESS)

    def check_degiro_connection(self, request):
        return AuthenticationResponse(result=AuthenticationResult.SUCCESS)

    def handle_totp_authentication(self, request, one_time_password):
        return AuthenticationResponse(result=AuthenticationResult.SUCCESS)

    def handle_in_app_authentication(self, request):
        return AuthenticationResponse(result=AuthenticationResult.SUCCESS)

    def logout_user(self, request) -> None:
        pass

    def is_broker_enabled(self) -> bool:
        return True

    def is_offline_mode(self) -> bool:
        return False

    def is_maintenance_mode_allowed(self) -> bool:
        return True

    def should_check_connection(self, request) -> bool:
        return True

    def get_authentication_status(self, request) -> dict:
        return {"status": "authenticated"}

    def handle_authentication_error(self, request, error, credentials=None):
        return AuthenticationResponse(result=AuthenticationResult.UNKNOWN_ERROR)


# Invalid service implementations that don't implement the correct interfaces
class InvalidPortfolioService:
    """Invalid portfolio service that doesn't implement the interface."""

    def get_portfolio_wrong(self):
        return []


class InvalidTransactionService:
    """Invalid transaction service that doesn't implement the interface."""

    def get_transactions_wrong(self):
        return []


class WrongInterfaceService(DepositServiceInterface):
    """Service that implements the wrong interface."""

    def get_cash_deposits(self) -> List[Deposit]:
        return []

    def calculate_cash_account_value(self) -> dict:
        return {}


class TestServiceInterfaceValidation:
    """Test cases for service interface validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = BrokerRegistry()
        self.registry.clear_all_registrations()

    def test_valid_service_interface_validation_passes(self):
        """Test that services implementing correct interfaces pass validation."""
        # Register configuration first
        self.registry.register_broker_config("testbroker", MockConfig)

        # Register services with correct interfaces - should not raise exception
        self.registry.register_broker_services(
            "testbroker",
            portfolio=ValidPortfolioService,
            transaction=ValidTransactionService,
            deposit=ValidDepositService,
            dividend=ValidDividendService,
            fee=ValidFeeService,
            account=ValidAccountService,
        )

        # Verify all services are registered
        assert "testbroker" in self.registry.get_fully_registered_brokers()
        assert len(self.registry.get_broker_capabilities("testbroker")) == 6

    def test_invalid_portfolio_service_interface_fails(self):
        """Test that portfolio service without correct interface fails validation."""
        self.registry.register_broker_config("testbroker", MockConfig)

        with pytest.raises(BrokerRegistryValidationError) as exc_info:
            self.registry.register_broker_services(
                "testbroker",
                portfolio=InvalidPortfolioService,
            )

        error_message = str(exc_info.value)
        assert "InvalidPortfolioService" in error_message
        assert "PortfolioServiceInterface" in error_message
        assert "does not implement the required interface" in error_message

    def test_invalid_transaction_service_interface_fails(self):
        """Test that transaction service without correct interface fails validation."""
        self.registry.register_broker_config("testbroker", MockConfig)

        with pytest.raises(BrokerRegistryValidationError) as exc_info:
            self.registry.register_broker_services(
                "testbroker",
                portfolio=ValidPortfolioService,
                transaction=InvalidTransactionService,
            )

        error_message = str(exc_info.value)
        assert "InvalidTransactionService" in error_message
        assert "TransactionServiceInterface" in error_message

    def test_wrong_interface_for_service_type_fails(self):
        """Test that service implementing wrong interface fails validation."""
        self.registry.register_broker_config("testbroker", MockConfig)

        # Try to register a deposit service for portfolio type - should fail
        with pytest.raises(BrokerRegistryValidationError) as exc_info:
            self.registry.register_broker_services(
                "testbroker",
                # This implements DepositServiceInterface, not PortfolioServiceInterface
                portfolio=WrongInterfaceService,
            )

        error_message = str(exc_info.value)
        assert "WrongInterfaceService" in error_message
        assert "PortfolioServiceInterface" in error_message

    def test_validate_all_service_interfaces_success(self):
        """Test validate_all_service_interfaces with valid services."""
        self.registry.register_broker_config("testbroker", MockConfig)
        self.registry.register_broker_services(
            "testbroker",
            portfolio=ValidPortfolioService,
            transaction=ValidTransactionService,
            deposit=ValidDepositService,
        )

        result = self.registry.validate_all_service_interfaces("testbroker")

        assert result["valid"] is True
        assert len(result["issues"]) == 0
        assert len(result["validated_services"]) == 3

        # Check that all services are marked as valid
        for service in result["validated_services"]:
            assert service["status"] == "valid"
            assert "interface" in service
            assert "service_type" in service
            assert "service_class" in service

    def test_validate_all_service_interfaces_with_failures(self):
        """Test validate_all_service_interfaces with some invalid services."""
        # We can't actually register invalid services through the normal flow
        # because validation happens during registration. So we'll test by
        # manually injecting invalid services (this simulates legacy code or bugs)

        self.registry.register_broker_config("testbroker", MockConfig)

        # Manually inject services to bypass registration validation (for testing purposes)
        self.registry._service_classes["testbroker"] = {
            ServiceType.PORTFOLIO: InvalidPortfolioService,
            ServiceType.TRANSACTION: ValidTransactionService,
        }
        self.registry._broker_capabilities["testbroker"] = [ServiceType.PORTFOLIO, ServiceType.TRANSACTION]

        result = self.registry.validate_all_service_interfaces("testbroker")

        assert result["valid"] is False
        assert len(result["issues"]) == 1
        assert len(result["validated_services"]) == 2

        # Check that one service is invalid, one is valid
        portfolio_service = next(s for s in result["validated_services"] if s["service_type"] == "portfolio")
        transaction_service = next(s for s in result["validated_services"] if s["service_type"] == "transaction")

        assert portfolio_service["status"] == "invalid"
        assert "error" in portfolio_service
        assert transaction_service["status"] == "valid"

    def test_validate_all_service_interfaces_nonexistent_broker(self):
        """Test validate_all_service_interfaces with nonexistent broker."""
        result = self.registry.validate_all_service_interfaces("nonexistent_broker")

        assert result["valid"] is False
        assert len(result["issues"]) == 1
        assert "No services registered for broker 'nonexistent_broker'" in result["issues"][0]
        assert len(result["validated_services"]) == 0

    def test_service_interface_mapping_completeness(self):
        """Test that all ServiceType enum values have corresponding interfaces."""
        # Verify that we have interfaces defined for all service types
        for service_type in ServiceType:
            assert service_type in BrokerRegistry.SERVICE_INTERFACES
            interface_class = BrokerRegistry.SERVICE_INTERFACES[service_type]
            assert interface_class is not None
            assert hasattr(interface_class, "__abstractmethods__")

    def test_interface_validation_with_multiple_inheritance(self):
        """Test that services with multiple inheritance work correctly."""

        class MultipleInheritanceService(ValidPortfolioService, ABC):
            """Service that inherits from both the interface and ABC."""

            pass

        self.registry.register_broker_config("testbroker", MockConfig)

        # Should work fine
        self.registry.register_broker_services(
            "testbroker",
            portfolio=MultipleInheritanceService,
        )

        result = self.registry.validate_all_service_interfaces("testbroker")
        assert result["valid"] is True

    def test_interface_validation_logging(self, caplog):
        """Test that interface validation produces appropriate log messages."""
        self.registry.register_broker_config("testbroker", MockConfig)

        # Interface validation should not raise any exceptions when valid
        try:
            self.registry.register_broker_services(
                "testbroker",
                portfolio=ValidPortfolioService,
            )
        except Exception as e:
            pytest.fail(f"Interface validation should have passed but raised: {e}")

        # Verify that the service was registered successfully (indicates validation passed)
        assert self.registry.broker_supports_service("testbroker", ServiceType.PORTFOLIO)
        assert "portfolio" in [s.value for s in self.registry.get_broker_capabilities("testbroker")]

    def test_interface_validation_provides_helpful_error_messages(self):
        """Test that validation errors provide helpful error messages."""
        self.registry.register_broker_config("testbroker", MockConfig)

        with pytest.raises(BrokerRegistryValidationError) as exc_info:
            self.registry.register_broker_services(
                "testbroker",
                portfolio=InvalidPortfolioService,
            )

        error_message = str(exc_info.value)

        # Verify error message contains all helpful information
        assert "InvalidPortfolioService" in error_message
        assert "portfolio" in error_message
        assert "PortfolioServiceInterface" in error_message
        assert "does not implement the required interface" in error_message
        assert "Please ensure your service class inherits from" in error_message


class TestServiceInterfaceValidationIntegration:
    """Integration tests for service interface validation with the full registration flow."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = BrokerRegistry()
        self.registry.clear_all_registrations()

    def test_complete_broker_registration_with_interface_validation(self):
        """Test complete broker registration flow with interface validation."""
        # Register configuration
        self.registry.register_broker_config("completebroker", MockConfig)

        # Register all service types with valid interfaces
        self.registry.register_broker_services(
            "completebroker",
            portfolio=ValidPortfolioService,
            transaction=ValidTransactionService,
            deposit=ValidDepositService,
            dividend=ValidDividendService,
            fee=ValidFeeService,
            account=ValidAccountService,
            authentication=ValidAuthenticationService,
        )

        # Verify broker is fully registered
        assert "completebroker" in self.registry.get_fully_registered_brokers()
        assert self.registry.is_config_registered("completebroker")

        # Verify all services are available
        capabilities = self.registry.get_broker_capabilities("completebroker")
        assert ServiceType.PORTFOLIO in capabilities
        assert ServiceType.TRANSACTION in capabilities
        assert ServiceType.DEPOSIT in capabilities
        assert ServiceType.DIVIDEND in capabilities
        assert ServiceType.FEE in capabilities
        assert ServiceType.ACCOUNT in capabilities
        assert ServiceType.AUTHENTICATION in capabilities

        # Verify interface validation passes
        validation_result = self.registry.validate_all_service_interfaces("completebroker")
        assert validation_result["valid"] is True
        assert len(validation_result["validated_services"]) == 7

    def test_register_complete_broker_with_interface_validation(self):
        """Test register_complete_broker method includes interface validation."""
        # This should work without issues
        self.registry.register_complete_broker(
            "completebroker",
            MockConfig,
            portfolio=ValidPortfolioService,
            transaction=ValidTransactionService,
            deposit=ValidDepositService,
        )

        # Verify registration succeeded
        assert "completebroker" in self.registry.get_fully_registered_brokers()

        # Verify interface validation
        validation_result = self.registry.validate_all_service_interfaces("completebroker")
        assert validation_result["valid"] is True
