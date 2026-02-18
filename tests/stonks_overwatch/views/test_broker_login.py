"""
Unit tests for BrokerLogin view.

This module tests the broker-specific login view that handles authentication
for different brokers (DEGIRO, Bitvavo, IBKR).
"""

from django.contrib.sessions.backends.db import SessionStore

from stonks_overwatch.constants import BrokerName
from stonks_overwatch.core.interfaces.authentication_service import AuthenticationResponse, AuthenticationResult
from stonks_overwatch.views.broker_login import BrokerLogin

import pytest
from django.test import RequestFactory, TestCase
from unittest.mock import Mock, patch


@pytest.mark.django_db
class TestBrokerLoginView(TestCase):
    """Test cases for BrokerLogin view."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.view = BrokerLogin()
        self.session = SessionStore()

        # Enable messages for testing

    def _add_messages_to_request(self, request):
        """Add messages storage to request for testing."""
        from django.contrib.messages.storage.fallback import FallbackStorage

        request._messages = FallbackStorage(request)

    @patch("stonks_overwatch.views.broker_login.BrokerRegistry")
    @patch("stonks_overwatch.views.broker_login.BrokerFactory")
    def test_get_degiro_login_shows_normal_state(self, mock_factory_class, mock_registry_class):
        """Test GET request for DEGIRO login shows normal login form."""
        # Mock the registry and factory
        mock_registry = Mock()
        mock_factory = Mock()
        mock_registry_class.return_value = mock_registry
        mock_factory_class.return_value = mock_factory

        # Mock broker validation
        mock_registry.get_registered_brokers.return_value = [
            BrokerName.DEGIRO.value,
            BrokerName.BITVAVO.value,
            BrokerName.IBKR.value,
        ]

        # Mock config
        mock_config = Mock()
        mock_config.is_enabled.return_value = True
        mock_factory.create_config.return_value = mock_config

        request = self.factory.get("/login/degiro/")
        request.session = self.session

        response = self.view.get(request, "degiro")

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "username" in content.lower() and "password" in content.lower()

    @patch("stonks_overwatch.views.broker_login.BrokerRegistry")
    @patch("stonks_overwatch.views.broker_login.BrokerFactory")
    def test_get_bitvavo_login_shows_api_fields(self, mock_factory_class, mock_registry_class):
        """Test GET request for Bitvavo login shows API key/secret fields."""
        # Mock the registry and factory
        mock_registry = Mock()
        mock_factory = Mock()
        mock_registry_class.return_value = mock_registry
        mock_factory_class.return_value = mock_factory

        # Mock broker validation
        mock_registry.get_registered_brokers.return_value = [
            BrokerName.DEGIRO.value,
            BrokerName.BITVAVO.value,
            BrokerName.IBKR.value,
        ]

        # Mock config
        mock_config = Mock()
        mock_config.is_enabled.return_value = True
        mock_factory.create_config.return_value = mock_config

        request = self.factory.get("/login/bitvavo/")
        request.session = self.session

        response = self.view.get(request, "bitvavo")

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "api key" in content.lower() and "api secret" in content.lower()

    @patch("stonks_overwatch.views.broker_login.BrokerRegistry")
    @patch("stonks_overwatch.views.broker_login.BrokerFactory")
    def test_get_invalid_broker_redirects(self, mock_factory_class, mock_registry_class):
        """Test GET request for invalid broker redirects to login."""
        # Mock the registry and factory
        mock_registry = Mock()
        mock_factory = Mock()
        mock_registry_class.return_value = mock_registry
        mock_factory_class.return_value = mock_factory

        # Mock broker validation - invalid broker not in list
        mock_registry.get_registered_brokers.return_value = [
            BrokerName.DEGIRO.value,
            BrokerName.BITVAVO.value,
            BrokerName.IBKR.value,
        ]

        request = self.factory.get("/login/invalid/")
        request.session = self.session
        self._add_messages_to_request(request)

        response = self.view.get(request, "invalid")

        assert response.status_code == 302
        assert response["Location"] == "/login"

    @patch("stonks_overwatch.jobs.jobs_scheduler.JobsScheduler.update_portfolio")
    @patch("stonks_overwatch.views.broker_login.BrokerRegistry")
    @patch("stonks_overwatch.views.broker_login.BrokerFactory")
    def test_post_update_portfolio_redirects(self, mock_factory_class, mock_registry_class, mock_update):
        """Test POST request with update_portfolio redirects to dashboard."""
        # Mock the registry and factory
        mock_registry = Mock()
        mock_factory = Mock()
        mock_registry_class.return_value = mock_registry
        mock_factory_class.return_value = mock_factory

        # Mock broker validation
        mock_registry.get_registered_brokers.return_value = [BrokerName.DEGIRO.value]

        request = self.factory.post("/login/degiro/", {"update_portfolio": "true"})
        request.session = self.session

        response = self.view.post(request, "degiro")

        assert response.status_code == 302
        assert response["Location"] == "/dashboard"
        mock_update.assert_called_once()

    @patch("stonks_overwatch.core.authentication_locator.get_authentication_service")
    @patch("stonks_overwatch.views.broker_login.BrokerRegistry")
    @patch("stonks_overwatch.views.broker_login.BrokerFactory")
    def test_post_degiro_successful_authentication_shows_loading(
        self, mock_factory_class, mock_registry_class, mock_get_auth_service
    ):
        """Test POST request with successful DEGIRO authentication shows loading screen."""
        # Mock the registry and factory
        mock_registry = Mock()
        mock_factory = Mock()
        mock_registry_class.return_value = mock_registry
        mock_factory_class.return_value = mock_factory

        # Mock broker validation
        mock_registry.get_registered_brokers.return_value = [BrokerName.DEGIRO.value]

        # Mock config
        mock_config = Mock()
        mock_factory.create_config.return_value = mock_config

        # Mock authentication service
        mock_auth_service = Mock()
        mock_get_auth_service.return_value = mock_auth_service

        # Mock successful authentication
        auth_response = AuthenticationResponse(result=AuthenticationResult.SUCCESS, session_id="test_session")
        mock_auth_service.authenticate_user.return_value = auth_response

        request = self.factory.post("/login/degiro/", {"username": "testuser", "password": "testpass"})
        request.session = self.session
        self._add_messages_to_request(request)

        response = self.view.post(request, "degiro")

        # Should show loading screen (200) instead of redirecting immediately
        assert response.status_code == 200
        # Should set authentication flag in session
        assert request.session.get("degiro_authenticated") is True
        mock_auth_service.authenticate_user.assert_called_once()

    @patch("stonks_overwatch.core.authentication_helper.AuthenticationHelper.is_broker_ready")
    @patch("stonks_overwatch.views.broker_login.BrokerRegistry")
    @patch("stonks_overwatch.views.broker_login.BrokerFactory")
    def test_post_bitvavo_successful_authentication(
        self, mock_factory_class, mock_registry_class, mock_is_broker_ready
    ):
        """Test POST request with successful Bitvavo authentication shows loading screen."""
        # Mock the registry and factory
        mock_registry = Mock()
        mock_factory = Mock()
        mock_registry_class.return_value = mock_registry
        mock_factory_class.return_value = mock_factory

        # Mock broker validation
        mock_registry.get_registered_brokers.return_value = [BrokerName.BITVAVO.value]

        # Mock config
        mock_config = Mock()
        mock_factory.create_config.return_value = mock_config

        # Mock Bitvavo authentication service via factory
        mock_auth_service = Mock()
        mock_factory.create_authentication_service.return_value = mock_auth_service

        # Mock successful authentication
        mock_auth_service.authenticate_user.return_value = {"success": True, "message": "Authentication successful"}

        # Mock broker is ready (has valid credentials)
        mock_is_broker_ready.return_value = True

        request = self.factory.post("/login/bitvavo/", {"username": "api_key", "password": "api_secret"})
        request.session = self.session
        self._add_messages_to_request(request)

        # Set up the view to use our mocked factory and registry
        self.view.factory = mock_factory
        self.view.registry = mock_registry

        response = self.view.post(request, "bitvavo")

        # Should show loading screen (200) instead of redirecting immediately
        assert response.status_code == 200
        # Should set authentication flag in session
        assert request.session.get("bitvavo_authenticated") is True
        mock_auth_service.authenticate_user.assert_called_once_with(
            request=request, api_key="api_key", api_secret="api_secret", remember_me=False
        )

    @patch("stonks_overwatch.jobs.jobs_scheduler.JobsScheduler.update_portfolio")
    @patch("stonks_overwatch.views.broker_login.BrokerRegistry")
    @patch("stonks_overwatch.views.broker_login.BrokerFactory")
    def test_post_bitvavo_portfolio_update_redirects_to_dashboard(
        self, mock_factory_class, mock_registry_class, mock_update_portfolio
    ):
        """Test POST request with update_portfolio redirects to dashboard."""
        # Mock the registry and factory
        mock_registry = Mock()
        mock_factory = Mock()
        mock_registry_class.return_value = mock_registry
        mock_factory_class.return_value = mock_factory

        # Mock broker validation
        mock_registry.get_registered_brokers.return_value = [BrokerName.BITVAVO.value]

        # Mock config
        mock_config = Mock()
        mock_factory.create_config.return_value = mock_config

        # Simulate authenticated session (loading screen scenario)
        request = self.factory.post("/login/bitvavo/", {"update_portfolio": "true"})
        request.session = self.session
        request.session["bitvavo_authenticated"] = True

        response = self.view.post(request, "bitvavo")

        # Should redirect to dashboard after portfolio update
        assert response.status_code == 302
        assert response["Location"] == "/dashboard"
        # Should call portfolio update
        mock_update_portfolio.assert_called_once()

    @patch("stonks_overwatch.core.authentication_locator.get_authentication_service")
    @patch("stonks_overwatch.views.broker_login.BrokerRegistry")
    @patch("stonks_overwatch.views.broker_login.BrokerFactory")
    def test_post_degiro_totp_required_shows_otp_form(
        self, mock_factory_class, mock_registry_class, mock_get_auth_service
    ):
        """Test POST request requiring TOTP shows OTP form."""
        # Mock the registry and factory
        mock_registry = Mock()
        mock_factory = Mock()
        mock_registry_class.return_value = mock_registry
        mock_factory_class.return_value = mock_factory

        # Mock broker validation
        mock_registry.get_registered_brokers.return_value = [BrokerName.DEGIRO.value]

        # Mock config
        mock_config = Mock()
        mock_factory.create_config.return_value = mock_config

        # Mock authentication service
        mock_auth_service = Mock()
        mock_get_auth_service.return_value = mock_auth_service

        # Mock TOTP required
        auth_response = AuthenticationResponse(result=AuthenticationResult.TOTP_REQUIRED, requires_totp=True)
        mock_auth_service.authenticate_user.return_value = auth_response

        request = self.factory.post("/login/degiro/", {"username": "testuser", "password": "testpass"})
        request.session = self.session
        self._add_messages_to_request(request)

        response = self.view.post(request, "degiro")

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "2fa" in content.lower() or "otp" in content.lower()

    @patch("stonks_overwatch.core.authentication_locator.get_authentication_service")
    @patch("stonks_overwatch.views.broker_login.BrokerRegistry")
    @patch("stonks_overwatch.views.broker_login.BrokerFactory")
    def test_post_degiro_totp_authentication_success(
        self, mock_factory_class, mock_registry_class, mock_get_auth_service
    ):
        """Test POST request with TOTP code for successful authentication."""
        # Mock the registry and factory
        mock_registry = Mock()
        mock_factory = Mock()
        mock_registry_class.return_value = mock_registry
        mock_factory_class.return_value = mock_factory

        # Mock broker validation
        mock_registry.get_registered_brokers.return_value = [BrokerName.DEGIRO.value]

        # Mock config
        mock_config = Mock()
        mock_factory.create_config.return_value = mock_config

        # Mock authentication service
        mock_auth_service = Mock()
        mock_get_auth_service.return_value = mock_auth_service

        # Mock successful TOTP authentication
        auth_response = AuthenticationResponse(result=AuthenticationResult.SUCCESS, session_id="test_session")
        mock_auth_service.handle_totp_authentication.return_value = auth_response

        request = self.factory.post("/login/degiro/", {"2fa_code": "123456"})
        request.session = self.session
        # Note: Credentials are stored by authentication service, not by the view
        self._add_messages_to_request(request)

        response = self.view.post(request, "degiro")

        # Should show loading screen (200) after successful TOTP authentication
        assert response.status_code == 200
        # Should set authentication flag in session and clear TOTP flag
        assert request.session.get("degiro_authenticated") is True
        assert request.session.get("degiro_totp_required") is False
        assert request.session.get("degiro_in_app_auth_required") is False
        mock_auth_service.handle_totp_authentication.assert_called_once_with(request, 123456)

    @patch("django.contrib.messages.error")
    @patch("stonks_overwatch.core.authentication_locator.get_authentication_service")
    @patch("stonks_overwatch.views.broker_login.BrokerRegistry")
    @patch("stonks_overwatch.views.broker_login.BrokerFactory")
    def test_post_degiro_invalid_credentials_shows_error(
        self, mock_factory_class, mock_registry_class, mock_get_auth_service, mock_messages
    ):
        """Test POST request with invalid credentials shows error."""
        # Mock the registry and factory
        mock_registry = Mock()
        mock_factory = Mock()
        mock_registry_class.return_value = mock_registry
        mock_factory_class.return_value = mock_factory

        # Mock broker validation
        mock_registry.get_registered_brokers.return_value = [BrokerName.DEGIRO.value]

        # Mock config
        mock_config = Mock()
        mock_factory.create_config.return_value = mock_config

        # Mock authentication service
        mock_auth_service = Mock()
        mock_get_auth_service.return_value = mock_auth_service

        # Mock invalid credentials
        auth_response = AuthenticationResponse(
            result=AuthenticationResult.INVALID_CREDENTIALS, message="Invalid username or password"
        )
        mock_auth_service.authenticate_user.return_value = auth_response

        request = self.factory.post("/login/degiro/", {"username": "testuser", "password": "wrongpass"})
        request.session = self.session

        response = self.view.post(request, "degiro")

        assert response.status_code == 200
        mock_messages.assert_called_once_with(request, "Invalid username or password")

    @patch("django.contrib.messages.error")
    @patch("stonks_overwatch.views.broker_login.BrokerRegistry")
    @patch("stonks_overwatch.views.broker_login.BrokerFactory")
    def test_post_missing_credentials_shows_error(self, mock_factory_class, mock_registry_class, mock_messages):
        """Test POST request with missing credentials shows error."""
        # Mock the registry and factory
        mock_registry = Mock()
        mock_factory = Mock()
        mock_registry_class.return_value = mock_registry
        mock_factory_class.return_value = mock_factory

        # Mock broker validation
        mock_registry.get_registered_brokers.return_value = [BrokerName.DEGIRO.value]

        request = self.factory.post("/login/degiro/", {})
        request.session = self.session

        response = self.view.post(request, "degiro")

        assert response.status_code == 200
        mock_messages.assert_called_once()
        # Check that credentials required message was called
        call_args = mock_messages.call_args[0]
        assert "required" in call_args[1].lower()

    def test_broker_display_names(self):
        """Test BrokerName enum provides correct display names."""
        assert BrokerName.DEGIRO.display_name == "DEGIRO"
        assert BrokerName.BITVAVO.display_name == "Bitvavo"
        assert BrokerName.IBKR.display_name == "Interactive Brokers"
        # Also test short names
        assert BrokerName.IBKR.short_name == "IBKR"
        assert BrokerName.DEGIRO.short_name == "DEGIRO"
        # Test __repr__() for debugging
        assert repr(BrokerName.DEGIRO) == "BrokerName.DEGIRO"
        assert repr(BrokerName.IBKR) == "BrokerName.IBKR"
        # Test __str__() returns value
        assert str(BrokerName.DEGIRO) == "degiro"
        assert str(BrokerName.IBKR) == "ibkr"

    def test_get_auth_fields_degiro(self):
        """Test _get_auth_fields returns correct fields for DEGIRO."""
        fields = self.view._get_auth_fields(BrokerName.DEGIRO)
        assert fields["username_label"] == "Username"
        assert fields["password_label"] == "Password"
        assert fields["supports_2fa"] is True
        assert fields["supports_remember_me"] is True

    def test_get_auth_fields_bitvavo(self):
        """Test _get_auth_fields returns correct fields for Bitvavo."""
        fields = self.view._get_auth_fields(BrokerName.BITVAVO)
        assert fields["username_label"] == "API Key"
        assert fields["password_label"] == "API Secret"
        assert fields["supports_2fa"] is False
        assert fields["supports_remember_me"] is True

    def test_get_auth_fields_ibkr(self):
        """Test _get_auth_fields returns correct fields for IBKR."""
        fields = self.view._get_auth_fields(BrokerName.IBKR)
        assert fields["access_token_label"] == "Access Token"
        assert fields["access_token_secret_label"] == "Access Token Secret"
        assert fields["consumer_key_label"] == "Consumer Key"
        assert fields["dh_prime_label"] == "DH Prime"
        assert fields["encryption_key_label"] == "Encryption Key (Optional)"
        assert fields["signature_key_label"] == "Signature Key (Optional)"
        assert fields["supports_2fa"] is False
        assert fields["supports_remember_me"] is True
        assert fields["auth_type"] == "oauth"

    def test_extract_degiro_credentials_valid_data(self):
        """Test _extract_degiro_credentials with valid form data."""
        request = self.factory.post(
            "/login/degiro/",
            {"username": "testuser", "password": "testpass", "2fa_code": "123456", "remember_me": "true"},
        )

        credentials = self.view._extract_degiro_credentials(request)

        assert credentials is not None
        assert credentials["username"] == "testuser"
        assert credentials["password"] == "testpass"
        assert credentials["one_time_password"] == 123456
        assert credentials["remember_me"] is True

    def test_extract_degiro_credentials_invalid_otp(self):
        """Test _extract_degiro_credentials with invalid OTP converts to None."""
        request = self.factory.post(
            "/login/degiro/", {"username": "testuser", "password": "testpass", "2fa_code": "invalid"}
        )

        credentials = self.view._extract_degiro_credentials(request)

        assert credentials is not None
        assert credentials["one_time_password"] is None

    def test_extract_degiro_credentials_missing_required(self):
        """Test _extract_degiro_credentials with missing required fields returns None."""
        request = self.factory.post("/login/degiro/", {"password": "testpass"})

        credentials = self.view._extract_degiro_credentials(request)

        assert credentials is None

    def test_extract_bitvavo_credentials_valid_data(self):
        """Test _extract_bitvavo_credentials with valid form data."""
        request = self.factory.post(
            "/login/bitvavo/", {"username": "api_key_123", "password": "api_secret_456", "remember_me": "true"}
        )

        credentials = self.view._extract_bitvavo_credentials(request)

        assert credentials is not None
        assert credentials["api_key"] == "api_key_123"
        assert credentials["api_secret"] == "api_secret_456"
        assert credentials["remember_me"] is True

    def test_extract_bitvavo_credentials_missing_required(self):
        """Test _extract_bitvavo_credentials with missing required fields returns None."""
        request = self.factory.post("/login/bitvavo/", {"username": "api_key_123"})

        credentials = self.view._extract_bitvavo_credentials(request)

        assert credentials is None

    def test_extract_ibkr_credentials_valid_data(self):
        """Test _extract_ibkr_credentials with valid OAuth form data."""
        request = self.factory.post(
            "/login/ibkr/",
            {
                "access_token": "valid_access_token_123",
                "access_token_secret": "valid_access_token_secret_123",
                "consumer_key": "valid_consumer_key",
                "dh_prime": "valid_dh_prime_value",
                "encryption_key": "optional_encryption_key",
                "signature_key": "optional_signature_key",
                "remember_me": "true",
            },
        )

        credentials = self.view._extract_ibkr_credentials(request)

        assert credentials is not None
        assert credentials["access_token"] == "valid_access_token_123"
        assert credentials["access_token_secret"] == "valid_access_token_secret_123"
        assert credentials["consumer_key"] == "valid_consumer_key"
        assert credentials["dh_prime"] == "valid_dh_prime_value"
        assert credentials["encryption_key"] == "optional_encryption_key"
        assert credentials["signature_key"] == "optional_signature_key"
        assert credentials["remember_me"] is True

    def test_extract_ibkr_credentials_missing_required(self):
        """Test _extract_ibkr_credentials with missing required OAuth fields returns None."""
        request = self.factory.post(
            "/login/ibkr/",
            {
                "access_token": "valid_token",
                "access_token_secret": "",  # Missing required field
                "consumer_key": "valid_key",
                "dh_prime": "valid_prime",
            },
        )

        credentials = self.view._extract_ibkr_credentials(request)

        assert credentials is None

    @patch("stonks_overwatch.core.authentication_locator.get_authentication_service")
    @patch("stonks_overwatch.views.broker_login.BrokerRegistry")
    @patch("stonks_overwatch.views.broker_login.BrokerFactory")
    def test_get_degiro_in_app_auth_required_shows_dialog(
        self, mock_factory_class, mock_registry_class, mock_get_auth_service
    ):
        """Test GET request when in-app authentication is required shows dialog."""
        # Mock the registry and factory
        mock_registry = Mock()
        mock_factory = Mock()
        mock_registry_class.return_value = mock_registry
        mock_factory_class.return_value = mock_factory

        # Mock broker validation
        mock_registry.get_registered_brokers.return_value = [BrokerName.DEGIRO.value]

        # Mock config
        mock_config = Mock()
        mock_factory.create_config.return_value = mock_config

        request = self.factory.get("/login/degiro/")
        request.session = self.session
        request.session["degiro_in_app_auth_required"] = True

        response = self.view.get(request, "degiro")

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "open the degiro app" in content.lower() or "mobile app" in content.lower()

    @patch("stonks_overwatch.core.authentication_locator.get_authentication_service")
    @patch("stonks_overwatch.views.broker_login.BrokerRegistry")
    @patch("stonks_overwatch.views.broker_login.BrokerFactory")
    def test_post_degiro_in_app_authentication_success(
        self, mock_factory_class, mock_registry_class, mock_get_auth_service
    ):
        """Test POST request with successful in-app authentication."""
        # Mock the registry and factory
        mock_registry = Mock()
        mock_factory = Mock()
        mock_registry_class.return_value = mock_registry
        mock_factory_class.return_value = mock_factory

        # Mock broker validation
        mock_registry.get_registered_brokers.return_value = [BrokerName.DEGIRO.value]

        # Mock config
        mock_config = Mock()
        mock_factory.create_config.return_value = mock_config

        # Mock authentication service
        mock_auth_service = Mock()
        mock_get_auth_service.return_value = mock_auth_service

        # Mock successful in-app authentication
        auth_response = AuthenticationResponse(result=AuthenticationResult.SUCCESS, session_id="test_session")
        mock_auth_service.handle_in_app_authentication.return_value = auth_response

        request = self.factory.post("/login/degiro/", {"in_app_auth": "true"})
        request.session = self.session
        self._add_messages_to_request(request)

        response = self.view.post(request, "degiro")

        assert response.status_code == 302
        assert response["Location"] == "/dashboard"
        mock_auth_service.handle_in_app_authentication.assert_called_once_with(request)

    @patch("django.contrib.messages.error")
    @patch("stonks_overwatch.core.authentication_locator.get_authentication_service")
    @patch("stonks_overwatch.views.broker_login.BrokerRegistry")
    @patch("stonks_overwatch.views.broker_login.BrokerFactory")
    def test_post_degiro_in_app_authentication_failure(
        self, mock_factory_class, mock_registry_class, mock_get_auth_service, mock_messages
    ):
        """Test POST request with failed in-app authentication."""
        # Mock the registry and factory
        mock_registry = Mock()
        mock_factory = Mock()
        mock_registry_class.return_value = mock_registry
        mock_factory_class.return_value = mock_factory

        # Mock broker validation
        mock_registry.get_registered_brokers.return_value = [BrokerName.DEGIRO.value]

        # Mock config
        mock_config = Mock()
        mock_factory.create_config.return_value = mock_config

        # Mock authentication service
        mock_auth_service = Mock()
        mock_get_auth_service.return_value = mock_auth_service

        # Mock failed in-app authentication
        auth_response = AuthenticationResponse(
            result=AuthenticationResult.INVALID_CREDENTIALS, message="In-app auth failed"
        )
        mock_auth_service.handle_in_app_authentication.return_value = auth_response

        request = self.factory.post("/login/degiro/", {"in_app_auth": "true"})
        request.session = self.session
        self._add_messages_to_request(request)

        response = self.view.post(request, "degiro")

        assert response.status_code == 200
        mock_messages.assert_called_once_with(request, "In-app auth failed")

    @patch("stonks_overwatch.core.authentication_locator.get_authentication_service")
    @patch("stonks_overwatch.views.broker_login.BrokerRegistry")
    @patch("stonks_overwatch.views.broker_login.BrokerFactory")
    def test_post_degiro_in_app_auth_required_flow(
        self, mock_factory_class, mock_registry_class, mock_get_auth_service
    ):
        """Test POST request that triggers in-app authentication requirement."""
        # Mock the registry and factory
        mock_registry = Mock()
        mock_factory = Mock()
        mock_registry_class.return_value = mock_registry
        mock_factory_class.return_value = mock_factory

        # Mock broker validation
        mock_registry.get_registered_brokers.return_value = [BrokerName.DEGIRO.value]

        # Mock config
        mock_config = Mock()
        mock_factory.create_config.return_value = mock_config

        # Mock authentication service
        mock_auth_service = Mock()
        mock_get_auth_service.return_value = mock_auth_service

        # Mock in-app auth required
        auth_response = AuthenticationResponse(result=AuthenticationResult.IN_APP_AUTHENTICATION_REQUIRED)
        mock_auth_service.authenticate_user.return_value = auth_response

        request = self.factory.post("/login/degiro/", {"username": "testuser", "password": "testpass"})
        request.session = self.session
        self._add_messages_to_request(request)

        response = self.view.post(request, "degiro")

        assert response.status_code == 200
        # Check that in-app auth flag is set in session
        assert request.session.get("degiro_in_app_auth_required") is True

    def test_extract_degiro_credentials_with_session_totp_flow(self):
        """Test _extract_degiro_credentials with TOTP flow returns only OTP."""
        # When only 2FA code is provided, the view returns just the OTP
        # The authentication service is responsible for retrieving stored credentials from session
        request = self.factory.post("/login/degiro/", {"2fa_code": "123456"})
        request.session = self.session

        credentials = self.view._extract_degiro_credentials(request)

        assert credentials is not None
        assert credentials["one_time_password"] == 123456
        # Note: username/password are NOT included - they will be retrieved by auth service
        assert "username" not in credentials
        assert "password" not in credentials

    def test_extract_degiro_credentials_totp_only_no_session(self):
        """Test _extract_degiro_credentials with TOTP returns OTP only."""
        # Same behavior regardless of session state - just return OTP
        # Authentication service handles retrieving stored credentials
        request = self.factory.post("/login/degiro/", {"2fa_code": "123456"})
        request.session = self.session

        credentials = self.view._extract_degiro_credentials(request)

        assert credentials is not None
        assert credentials["one_time_password"] == 123456

    @patch("stonks_overwatch.core.authentication_locator.get_authentication_service")
    @patch("stonks_overwatch.views.broker_login.BrokerRegistry")
    @patch("stonks_overwatch.views.broker_login.BrokerFactory")
    def test_authenticate_degiro_stores_credentials_on_totp_required(
        self, mock_factory_class, mock_registry_class, mock_get_auth_service
    ):
        """Test that DEGIRO authentication calls auth service correctly when TOTP is required."""
        # Mock the registry and factory
        mock_registry = Mock()
        mock_factory = Mock()
        mock_registry_class.return_value = mock_registry
        mock_factory_class.return_value = mock_factory

        # Mock broker validation
        mock_registry.get_registered_brokers.return_value = [BrokerName.DEGIRO.value]

        # Mock config
        mock_config = Mock()
        mock_factory.create_config.return_value = mock_config

        # Mock authentication service
        mock_auth_service = Mock()
        mock_get_auth_service.return_value = mock_auth_service

        # Mock TOTP required response
        auth_response = AuthenticationResponse(result=AuthenticationResult.TOTP_REQUIRED)
        mock_auth_service.authenticate_user.return_value = auth_response

        request = self.factory.post(
            "/login/degiro/", {"username": "testuser", "password": "testpass", "remember_me": "true"}
        )
        request.session = self.session
        self._add_messages_to_request(request)

        _response = self.view.post(request, "degiro")

        # Verify authentication service was called with correct credentials
        mock_auth_service.authenticate_user.assert_called_once_with(
            request=request, username="testuser", password="testpass", one_time_password=None, remember_me=True
        )

        # Verify TOTP required flag is set correctly
        assert request.session.get("degiro_totp_required") is True
        assert request.session.get("degiro_in_app_auth_required") is False

        # Note: Credentials are now stored by the authentication service itself
        # in the correct session key (not "degiro_credentials")

    @patch("stonks_overwatch.core.authentication_helper.AuthenticationHelper.is_broker_ready")
    def test_authenticate_ibkr_success(self, mock_is_broker_ready):
        """Test IBKR authentication success with OAuth credentials."""
        # Mock the view's factory and registry
        mock_factory = Mock()
        mock_registry = Mock()
        mock_config = Mock()

        mock_factory.create_config.return_value = mock_config
        mock_registry.get_registered_brokers.return_value = [BrokerName.IBKR.value]

        self.view.factory = mock_factory
        self.view.registry = mock_registry

        # Mock IBKR authentication service via factory
        mock_auth_service = Mock()
        mock_factory.create_authentication_service.return_value = mock_auth_service
        mock_auth_service.authenticate_user.return_value = {"success": True, "message": "Authentication successful"}

        # Mock broker is ready (has valid credentials)
        mock_is_broker_ready.return_value = True

        # Test valid OAuth credentials
        request = self.factory.post(
            "/login/ibkr/",
            {
                "access_token": "valid_access_token_123",
                "access_token_secret": "valid_access_token_secret_123",
                "consumer_key": "valid_consumer_key",
                "dh_prime": "valid_dh_prime_value",
            },
        )
        request.session = self.session
        self._add_messages_to_request(request)

        response = self.view.post(request, "ibkr")

        # IBKR now shows loading screen (200) like degiro/bitvavo
        assert response.status_code == 200
        # Should set authentication flag in session
        assert request.session.get("ibkr_authenticated") is True
        # Verify authentication service was called
        mock_auth_service.authenticate_user.assert_called_once()

    def test_authenticate_ibkr_invalid_credentials(self):
        """Test IBKR authentication with invalid OAuth credentials."""
        # Mock the view's factory and registry
        mock_factory = Mock()
        mock_registry = Mock()
        mock_config = Mock()

        mock_factory.create_config.return_value = mock_config
        mock_registry.get_registered_brokers.return_value = [BrokerName.IBKR.value]

        self.view.factory = mock_factory
        self.view.registry = mock_registry

        # Mock IBKR authentication service via factory
        mock_auth_service = Mock()
        mock_factory.create_authentication_service.return_value = mock_auth_service
        mock_auth_service.authenticate_user.return_value = {"success": False, "message": "Invalid OAuth credentials"}

        # Test invalid credentials (all required fields present but invalid)
        request = self.factory.post(
            "/login/ibkr/",
            {
                "access_token": "invalid_token",
                "access_token_secret": "invalid_secret",
                "consumer_key": "invalid_key",
                "dh_prime": "invalid_prime",
            },
        )
        request.session = self.session
        self._add_messages_to_request(request)

        response = self.view.post(request, "ibkr")

        assert response.status_code == 200
        # Verify authentication service was called with the invalid credentials
        mock_auth_service.authenticate_user.assert_called_once()

    @patch("django.contrib.messages.error")
    def test_authenticate_ibkr_missing_credentials(self, mock_messages):
        """Test IBKR authentication with missing OAuth credentials."""
        # Mock the view's factory directly (should not be called)
        mock_factory = Mock()
        mock_auth_service = Mock()
        mock_factory.create_authentication_service.return_value = mock_auth_service
        self.view.factory = mock_factory

        # Mock the registry
        mock_registry = Mock()
        mock_registry.get_registered_brokers.return_value = [BrokerName.IBKR.value]
        self.view.registry = mock_registry

        # Test missing credentials (empty required fields)
        request = self.factory.post(
            "/login/ibkr/", {"access_token": "", "access_token_secret": "", "consumer_key": "", "dh_prime": ""}
        )
        request.session = self.session
        self._add_messages_to_request(request)

        response = self.view.post(request, "ibkr")

        assert response.status_code == 200
        mock_messages.assert_called_once_with(
            request, "OAuth credentials are required (access token, access token secret, consumer key, and DH prime)."
        )

        # Verify authentication service was NOT called since credentials were missing
        mock_auth_service.authenticate_user.assert_not_called()

    @patch("django.contrib.messages.error")
    @patch("stonks_overwatch.views.broker_login.BrokerRegistry")
    @patch("stonks_overwatch.views.broker_login.BrokerFactory")
    def test_authenticate_bitvavo_failure(self, mock_factory_class, mock_registry_class, mock_messages):
        """Test Bitvavo authentication failure."""
        # Mock the registry and factory
        mock_registry = Mock()
        mock_factory = Mock()
        mock_registry_class.return_value = mock_registry
        mock_factory_class.return_value = mock_factory

        # Mock broker validation
        mock_registry.get_registered_brokers.return_value = [BrokerName.BITVAVO.value]

        # Mock config
        mock_config = Mock()
        mock_factory.create_config.return_value = mock_config

        # Mock Bitvavo authentication service via factory
        mock_auth_service = Mock()
        mock_factory.create_authentication_service.return_value = mock_auth_service

        # Mock failed authentication
        mock_auth_service.authenticate_user.return_value = {"success": False, "message": "Invalid API credentials"}

        request = self.factory.post("/login/bitvavo/", {"username": "invalid_key", "password": "invalid_secret"})
        request.session = self.session
        self._add_messages_to_request(request)

        # Set up the view to use our mocked factory and registry
        self.view.factory = mock_factory
        self.view.registry = mock_registry

        response = self.view.post(request, "bitvavo")

        assert response.status_code == 200
        mock_messages.assert_called_once_with(request, "Invalid API credentials")

    def test_check_totp_required_degiro(self):
        """Test _check_totp_required for DEGIRO."""
        request = self.factory.get("/login/degiro/")
        request.session = self.session
        request.session["degiro_totp_required"] = True

        result = self.view._check_totp_required(request, BrokerName.DEGIRO)
        assert result is True

        # Test without session flag
        request.session["degiro_totp_required"] = False
        result = self.view._check_totp_required(request, BrokerName.DEGIRO)
        assert result is False

    def test_check_totp_required_other_brokers(self):
        """Test _check_totp_required for non-DEGIRO brokers."""
        request = self.factory.get("/login/bitvavo/")
        request.session = self.session

        result = self.view._check_totp_required(request, BrokerName.BITVAVO)
        assert result is False

        result = self.view._check_totp_required(request, BrokerName.IBKR)
        assert result is False

    def test_check_in_app_auth_required_degiro(self):
        """Test _check_in_app_auth_required for DEGIRO."""
        request = self.factory.get("/login/degiro/")
        request.session = self.session
        request.session["degiro_in_app_auth_required"] = True

        result = self.view._check_in_app_auth_required(request, BrokerName.DEGIRO)
        assert result is True

        # Test without session flag
        request.session["degiro_in_app_auth_required"] = False
        result = self.view._check_in_app_auth_required(request, BrokerName.DEGIRO)
        assert result is False

    def test_check_in_app_auth_required_other_brokers(self):
        """Test _check_in_app_auth_required for non-DEGIRO brokers."""
        request = self.factory.get("/login/bitvavo/")
        request.session = self.session

        result = self.view._check_in_app_auth_required(request, BrokerName.BITVAVO)
        assert result is False

        result = self.view._check_in_app_auth_required(request, BrokerName.IBKR)
        assert result is False

    @patch("stonks_overwatch.core.authentication_helper.AuthenticationHelper.is_broker_ready")
    @patch("stonks_overwatch.views.broker_login.BrokerFactory")
    def test_check_authenticated(self, mock_factory_class, mock_is_broker_ready):
        """Test _check_authenticated for all brokers."""
        # Setup mocks
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        self.view.factory = mock_factory

        mock_config = Mock()
        mock_config.is_enabled.return_value = True
        mock_factory.create_config.return_value = mock_config
        mock_is_broker_ready.return_value = True

        request = self.factory.get("/login/degiro/")
        request.session = self.session

        # Test DEGIRO
        request.session["degiro_authenticated"] = True
        result = self.view._check_authenticated(request, BrokerName.DEGIRO)
        assert result is True

        # Test Bitvavo
        request.session["bitvavo_authenticated"] = True
        result = self.view._check_authenticated(request, BrokerName.BITVAVO)
        assert result is True

        # Test IBKR
        request.session["ibkr_authenticated"] = True
        result = self.view._check_authenticated(request, BrokerName.IBKR)
        assert result is True

        # Test without authentication
        request.session.clear()
        result = self.view._check_authenticated(request, BrokerName.DEGIRO)
        assert result is False

        # Test with session but without valid credentials
        request.session["degiro_authenticated"] = True
        mock_is_broker_ready.return_value = False
        result = self.view._check_authenticated(request, BrokerName.DEGIRO)
        assert result is False
