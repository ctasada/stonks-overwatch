"""
Unit tests for AuthenticationMiddleware.

This module tests the general authentication middleware that handles
authentication logic for all brokers.
"""

from django.http import HttpRequest, HttpResponse

from stonks_overwatch.constants import BrokerName
from stonks_overwatch.middleware.authentication import AuthenticationMiddleware

from django.test import TestCase
from unittest.mock import Mock, patch


class TestAuthenticationMiddleware(TestCase):
    """Test cases for AuthenticationMiddleware."""

    @patch("stonks_overwatch.middleware.authentication.BrokerRegistry")
    @patch("stonks_overwatch.middleware.authentication.BrokerFactory")
    @patch("stonks_overwatch.middleware.authentication.get_authentication_service")
    def setUp(self, mock_get_auth_service, mock_factory_class, mock_registry_class):
        """Set up test fixtures."""
        self.get_response = Mock(return_value=HttpResponse())
        self.mock_auth_service = Mock()
        self.mock_factory = Mock()
        self.mock_registry = Mock()

        mock_get_auth_service.return_value = self.mock_auth_service
        mock_factory_class.return_value = self.mock_factory
        mock_registry_class.return_value = self.mock_registry

        # Default mock behavior
        self.mock_registry.get_registered_brokers.return_value = []

        self.middleware = AuthenticationMiddleware(self.get_response)
        self.request = self._create_mock_request()

    def _create_mock_request(self):
        """Create a mock request with session."""
        request = Mock(spec=HttpRequest)
        request.session = {}
        request.path_info = "/dashboard/"
        return request

    def test_is_public_url_method(self):
        """Test _is_public_url method correctly identifies public URLs."""
        assert self.middleware._is_public_url("login") is True
        assert self.middleware._is_public_url("settings") is True
        assert self.middleware._is_public_url("release_notes") is True
        assert self.middleware._is_public_url("dashboard") is False
        assert self.middleware._is_public_url(None) is False

    @patch("stonks_overwatch.middleware.authentication.resolve")
    def test_middleware_allows_public_urls(self, mock_resolve):
        """Test middleware allows access to public URLs without authentication."""
        mock_resolve.return_value.url_name = "login"

        response = self.middleware(self.request)

        assert response == self.get_response.return_value
        # Should not check authentication for public URLs

    @patch("stonks_overwatch.middleware.authentication.resolve")
    @patch("stonks_overwatch.middleware.authentication.redirect")
    def test_middleware_redirects_to_login_when_no_brokers_configured(self, mock_redirect, mock_resolve):
        """Test middleware redirects even if session is 'ok' but no brokers are validly configured."""
        mock_resolve.return_value.url_name = "dashboard"
        mock_redirect.return_value = HttpResponse(status=302)

        # Mock no configured brokers
        self.mock_registry.get_registered_brokers.return_value = []

        response = self.middleware(self.request)

        assert response.status_code == 302
        mock_redirect.assert_called_once_with("login")

    @patch("stonks_overwatch.middleware.authentication.resolve")
    @patch("stonks_overwatch.services.utilities.credential_validator.CredentialValidator.has_valid_credentials")
    def test_middleware_checks_authentication_when_brokers_configured(self, mock_has_valid_credentials, mock_resolve):
        """Test middleware checks authentication when brokers are configured."""
        mock_resolve.return_value.url_name = "dashboard"

        # Mock configured broker - return BrokerName enum
        self.mock_registry.get_registered_brokers.return_value = [BrokerName.DEGIRO]
        mock_config = Mock()
        mock_config.is_enabled.return_value = True
        mock_credentials = Mock()
        mock_credentials.username = "testuser"
        mock_credentials.password = "testpass"
        mock_config.get_credentials = mock_credentials
        # Ensure offline_mode is False so demo mode is not detected
        mock_config.offline_mode = False
        self.mock_factory.create_config.return_value = mock_config

        # Mock valid credentials
        mock_has_valid_credentials.return_value = True

        # Set broker-specific session key to indicate authentication
        from stonks_overwatch.utils.core.session_keys import SessionKeys

        self.request.session[SessionKeys.get_authenticated_key(BrokerName.DEGIRO)] = True

        # Mock offline and maintenance mode
        self.mock_auth_service.is_offline_mode.return_value = False
        self.mock_auth_service.is_maintenance_mode_allowed.return_value = True

        # Mock demo mode detection to return False
        with patch("stonks_overwatch.utils.core.demo_mode.is_demo_mode", return_value=False):
            response = self.middleware(self.request)

        assert response == self.get_response.return_value

    @patch("stonks_overwatch.middleware.authentication.resolve")
    @patch("stonks_overwatch.middleware.authentication.redirect")
    @patch("stonks_overwatch.services.utilities.credential_validator.CredentialValidator.has_valid_credentials")
    def test_middleware_redirects_unauthenticated_user(self, mock_has_valid_credentials, mock_redirect, mock_resolve):
        """Test middleware redirects unauthenticated users to login."""
        mock_resolve.return_value.url_name = "dashboard"
        mock_redirect.return_value = HttpResponse(status=302)

        # Mock configured broker - return BrokerName enum
        self.mock_registry.get_registered_brokers.return_value = [BrokerName.DEGIRO]
        mock_config = Mock()
        mock_config.is_enabled.return_value = True
        mock_credentials = Mock()
        mock_credentials.username = "testuser"
        mock_credentials.password = "testpass"
        mock_config.get_credentials = mock_credentials
        # Ensure offline_mode is False so demo mode is not detected
        mock_config.offline_mode = False
        self.mock_factory.create_config.return_value = mock_config

        # Mock valid credentials
        mock_has_valid_credentials.return_value = True

        # Leave session without authentication key to simulate unauthenticated user
        # (request.session is empty by default)
        self.mock_auth_service.is_offline_mode.return_value = False

        # Mock demo mode detection to return False
        with patch("stonks_overwatch.utils.core.demo_mode.is_demo_mode", return_value=False):
            response = self.middleware(self.request)

        assert response.status_code == 302
        mock_redirect.assert_called_once_with("login")
        self.mock_auth_service.logout_user.assert_called_once_with(self.request)

    @patch("stonks_overwatch.middleware.authentication.resolve")
    @patch("stonks_overwatch.middleware.authentication.is_demo_mode")
    def test_middleware_bypasses_authentication_in_demo_mode(self, mock_is_demo_mode, mock_resolve):
        """Test middleware bypasses authentication checks when in demo mode."""
        mock_resolve.return_value.url_name = "dashboard"
        mock_is_demo_mode.return_value = True

        response = self.middleware(self.request)

        assert response == self.get_response.return_value
        # Should not check authentication in demo mode
