"""
Tests for IBKR authentication service.

This module tests the IBKR authentication service implementation.
"""

from stonks_overwatch.config.ibkr import IbkrConfig, IbkrCredentials
from stonks_overwatch.constants import BrokerName
from stonks_overwatch.core.interfaces.authentication_service import (
    AuthenticationResult,
)
from stonks_overwatch.services.brokers.ibkr.services.authentication_service import (
    IbkrAuthenticationService,
)

from django.test import RequestFactory
from unittest.mock import patch


class TestIbkrAuthenticationService:
    """Test cases for IBKR authentication service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.request.session = {}

        # Create test credentials
        self.credentials = IbkrCredentials(
            access_token="test_access_token_123",
            access_token_secret="test_access_token_secret_123",
            consumer_key="test_consumer_key",
            dh_prime="test_dh_prime_value",
            encryption_key="fake_encryption_key",
            signature_key="fake_signature_key",
        )

        # Create test config
        self.config = IbkrConfig(
            credentials=self.credentials,
            start_date="2020-01-01",
            enabled=True,
            offline_mode=False,
        )

        # Create service instance
        self.service = IbkrAuthenticationService(config=self.config)

    def test_broker_name(self):
        """Test that broker name is correctly set."""
        assert self.service.broker_name == BrokerName.IBKR

    def test_validate_credentials_success(self):
        """Test successful credential validation."""
        result = self.service.validate_credentials(
            access_token="valid_access_token_123",
            access_token_secret="valid_access_token_secret_123",
            consumer_key="valid_consumer_key",
            dh_prime="valid_dh_prime_value",
        )

        assert result["success"] is True
        assert "validated successfully" in result["message"]
        assert "account_info" in result
        assert "consumer_key" in result["account_info"]

    def test_validate_credentials_missing_required(self):
        """Test credential validation with missing required fields."""
        result = self.service.validate_credentials(
            access_token="",
            access_token_secret="valid_secret",
            consumer_key="valid_key",
            dh_prime="valid_prime",
        )

        assert result["success"] is False
        assert "Missing required OAuth credentials" in result["message"]

    def test_validate_credentials_invalid_format(self):
        """Test credential validation with invalid token format."""
        result = self.service.validate_credentials(
            access_token="short",  # Too short
            access_token_secret="also_short",  # Too short
            consumer_key="valid_consumer_key",
            dh_prime="valid_dh_prime_value",
        )

        assert result["success"] is False
        assert "Invalid token format" in result["message"]

    @patch(
        "stonks_overwatch.services.brokers.ibkr.services.authentication_service.IbkrAuthenticationService._ensure_broker_configuration"
    )
    @patch(
        "stonks_overwatch.services.brokers.ibkr.services.authentication_service.IbkrAuthenticationService._clear_broker_cache"
    )
    @patch(
        "stonks_overwatch.services.brokers.ibkr.services.authentication_service.IbkrAuthenticationService._reset_ibkr_client"
    )
    @patch(
        "stonks_overwatch.services.brokers.ibkr.services.authentication_service.IbkrAuthenticationService._reconfigure_jobs"
    )
    @patch(
        "stonks_overwatch.services.brokers.ibkr.services.authentication_service.IbkrAuthenticationService._trigger_portfolio_update"
    )
    @patch(
        "stonks_overwatch.services.brokers.ibkr.services.authentication_service.IbkrAuthenticationService.validate_credentials"
    )
    def test_authenticate_user_success(
        self,
        mock_validate_credentials,
        mock_trigger_update,
        mock_reconfigure_jobs,
        mock_reset_client,
        mock_clear_cache,
        mock_ensure_config,
    ):
        """Test successful user authentication."""
        # Setup validation to succeed
        mock_validate_credentials.return_value = {"success": True, "message": "Valid", "account_info": {"id": "123"}}

        result = self.service.authenticate_user(
            request=self.request,
            access_token="valid_access_token_123",
            access_token_secret="valid_access_token_secret_123",
            consumer_key="valid_consumer_key",
            dh_prime="valid_dh_prime_value",
            remember_me=True,
        )

        assert result["success"] is True
        assert "Authentication successful" in result["message"]
        assert "account_info" in result

        # Verify validation was called
        mock_validate_credentials.assert_called_once()

        # Verify session was set
        assert self.request.session.get("ibkr_authenticated") is True
        assert "ibkr_credentials" in self.request.session

        # Verify helper methods were called
        mock_ensure_config.assert_called_once()
        mock_clear_cache.assert_called_once()
        mock_reset_client.assert_called_once()
        mock_reconfigure_jobs.assert_called_once()
        mock_trigger_update.assert_called_once()

    def test_authenticate_user_invalid_credentials(self):
        """Test user authentication with invalid credentials."""
        # Using self.service directly which uses validation logic logic
        # Here we rely on valididation check first
        result = self.service.authenticate_user(
            request=self.request,
            access_token="",  # Invalid
            access_token_secret="valid_secret",
            consumer_key="valid_key",
            dh_prime="valid_prime",
        )

        assert result["success"] is False
        assert "Missing required OAuth credentials" in result["message"]

    def test_is_user_authenticated_true(self):
        """Test is_user_authenticated returns True for authenticated user."""
        # Set up authenticated session
        self.request.session["ibkr_authenticated"] = True
        self.request.session["ibkr_credentials"] = {
            "access_token": "valid_access_token_123",
            "access_token_secret": "valid_access_token_secret_123",
            "consumer_key": "valid_consumer_key",
            "dh_prime": "valid_dh_prime_value",
        }

        result = self.service.is_user_authenticated(self.request)
        assert result is True

    def test_is_user_authenticated_false_no_session(self):
        """Test is_user_authenticated returns False when not authenticated."""
        result = self.service.is_user_authenticated(self.request)
        assert result is False

    def test_is_user_authenticated_false_no_credentials(self):
        """Test is_user_authenticated returns False when credentials missing."""
        self.request.session["ibkr_authenticated"] = True
        # No credentials in session

        result = self.service.is_user_authenticated(self.request)
        assert result is False

    def test_logout_user_success(self):
        """Test successful user logout."""
        # Set up authenticated session
        self.request.session["ibkr_authenticated"] = True
        self.request.session["ibkr_credentials"] = {"test": "data"}
        self.request.session["ibkr_totp_required"] = True
        self.request.session["ibkr_in_app_auth_required"] = True

        result = self.service.logout_user(self.request)

        assert result is True
        assert "ibkr_authenticated" not in self.request.session
        assert "ibkr_credentials" not in self.request.session
        assert "ibkr_totp_required" not in self.request.session
        assert "ibkr_in_app_auth_required" not in self.request.session

    def test_is_offline_mode(self):
        """Test is_offline_mode returns config value."""
        assert self.service.is_offline_mode() is False

        # Test with offline mode enabled
        offline_config = IbkrConfig(
            credentials=self.credentials,
            start_date="2020-01-01",
            enabled=True,
            offline_mode=True,
        )
        offline_service = IbkrAuthenticationService(config=offline_config)
        assert offline_service.is_offline_mode() is True

    def test_get_authentication_status(self):
        """Test get_authentication_status returns correct information."""
        # Set up authenticated session with all required OAuth credentials
        self.request.session["ibkr_authenticated"] = True
        self.request.session["ibkr_credentials"] = {
            "access_token": "test_access_token_123",
            "access_token_secret": "test_access_token_secret_123",
            "consumer_key": "test_consumer_key",
            "dh_prime": "test_dh_prime_value",
        }

        status = self.service.get_authentication_status(self.request)

        assert status["broker"] == BrokerName.IBKR
        assert status["is_authenticated"] is True
        assert status["has_session_credentials"] is True
        assert status["has_consumer_key"] is True
        assert status["offline_mode"] is False
        assert status["config_enabled"] is True

    def test_handle_authentication_error(self):
        """Test authentication error handling."""
        error = Exception("unauthorized access")
        response = self.service.handle_authentication_error(self.request, error)

        assert response.result == AuthenticationResult.INVALID_CREDENTIALS
        assert "Invalid OAuth credentials" in response.message

    def test_degiro_specific_methods_not_applicable(self):
        """Test that DeGiro-specific methods return appropriate responses."""
        # These methods should indicate they're not applicable for IBKR
        response = self.service.check_degiro_connection(self.request)
        assert response.result == AuthenticationResult.CONFIGURATION_ERROR
        assert "not applicable for IBKR" in response.message

        response = self.service.handle_totp_authentication(self.request, 123456)
        assert response.result == AuthenticationResult.CONFIGURATION_ERROR
        assert "not supported for IBKR" in response.message

        response = self.service.handle_in_app_authentication(self.request)
        assert response.result == AuthenticationResult.CONFIGURATION_ERROR
        assert "not supported for IBKR" in response.message

        assert self.service.is_degiro_enabled() is False


class TestIbkrAuthenticationServiceIntegration:
    """Integration tests for IBKR authentication service."""

    def test_can_be_created_via_factory(self):
        """Test that the service can be created via BrokerFactory."""
        from stonks_overwatch.core.factories.broker_factory import BrokerFactory
        from stonks_overwatch.core.service_types import ServiceType

        factory = BrokerFactory()
        service = factory.create_service(BrokerName.IBKR, ServiceType.AUTHENTICATION)

        assert service is not None
        assert isinstance(service, IbkrAuthenticationService)
        assert service.broker_name == BrokerName.IBKR

    def test_can_be_created_directly_with_config(self):
        """Test that the service can be created directly with config."""
        from stonks_overwatch.core.factories.broker_factory import BrokerFactory

        factory = BrokerFactory()
        config = factory.create_config(BrokerName.IBKR)

        # Service can be instantiated directly with config
        service = IbkrAuthenticationService(config=config)

        assert service is not None
        assert isinstance(service, IbkrAuthenticationService)
        assert service.broker_name == BrokerName.IBKR
