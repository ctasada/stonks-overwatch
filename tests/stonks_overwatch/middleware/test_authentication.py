"""
Unit tests for AuthenticationMiddleware.

This module tests the general authentication middleware that handles
authentication logic for all brokers.
"""

from django.http import HttpRequest, HttpResponse

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
        self.mock_auth_service.is_user_authenticated.assert_not_called()

    @patch("stonks_overwatch.middleware.authentication.resolve")
    def test_middleware_allows_access_when_no_brokers_configured(self, mock_resolve):
        """Test middleware allows access when no brokers are configured."""
        mock_resolve.return_value.url_name = "dashboard"

        # Mock no configured brokers
        self.mock_registry.get_registered_brokers.return_value = []

        response = self.middleware(self.request)

        assert response == self.get_response.return_value
        # Should not check authentication when no brokers configured
        self.mock_auth_service.is_user_authenticated.assert_not_called()

    @patch("stonks_overwatch.middleware.authentication.resolve")
    def test_middleware_checks_authentication_when_brokers_configured(self, mock_resolve):
        """Test middleware checks authentication when brokers are configured."""
        mock_resolve.return_value.url_name = "dashboard"

        # Mock configured broker
        self.mock_registry.get_registered_brokers.return_value = ["degiro"]
        mock_config = Mock()
        mock_config.is_enabled.return_value = True
        mock_credentials = Mock()
        mock_credentials.username = "testuser"
        mock_credentials.password = "testpass"
        mock_config.get_credentials = mock_credentials
        self.mock_factory.create_config.return_value = mock_config

        # Mock authenticated user
        self.mock_auth_service.is_user_authenticated.return_value = True
        self.mock_auth_service.is_offline_mode.return_value = False
        self.mock_auth_service.is_maintenance_mode_allowed.return_value = True

        response = self.middleware(self.request)

        assert response == self.get_response.return_value
        # Should check authentication when brokers are configured
        self.mock_auth_service.is_user_authenticated.assert_called_once()

    @patch("stonks_overwatch.middleware.authentication.resolve")
    @patch("stonks_overwatch.middleware.authentication.redirect")
    def test_middleware_redirects_unauthenticated_user(self, mock_redirect, mock_resolve):
        """Test middleware redirects unauthenticated users to login."""
        mock_resolve.return_value.url_name = "dashboard"
        mock_redirect.return_value = HttpResponse(status=302)

        # Mock configured broker
        self.mock_registry.get_registered_brokers.return_value = ["degiro"]
        mock_config = Mock()
        mock_config.is_enabled.return_value = True
        mock_credentials = Mock()
        mock_credentials.username = "testuser"
        mock_credentials.password = "testpass"
        mock_config.get_credentials = mock_credentials
        self.mock_factory.create_config.return_value = mock_config

        # Mock unauthenticated user
        self.mock_auth_service.is_user_authenticated.return_value = False
        self.mock_auth_service.is_offline_mode.return_value = False

        response = self.middleware(self.request)

        assert response.status_code == 302
        mock_redirect.assert_called_once_with("login")
        self.mock_auth_service.logout_user.assert_called_once_with(self.request)

    def test_has_valid_credentials_degiro(self):
        """Test _has_valid_credentials correctly validates DEGIRO credentials."""
        # Valid credentials
        mock_credentials = Mock()
        mock_credentials.username = "testuser"
        mock_credentials.password = "testpass"

        assert self.middleware._has_valid_credentials("degiro", mock_credentials) is True

        # Invalid credentials (placeholders)
        mock_credentials.username = "USERNAME"
        mock_credentials.password = "PASSWORD"

        assert self.middleware._has_valid_credentials("degiro", mock_credentials) is False

        # Too short credentials
        mock_credentials.username = "ab"
        mock_credentials.password = "cd"

        assert self.middleware._has_valid_credentials("degiro", mock_credentials) is False

    def test_has_valid_credentials_bitvavo(self):
        """Test _has_valid_credentials correctly validates Bitvavo credentials."""
        # Valid credentials
        mock_credentials = Mock()
        mock_credentials.apikey = "valid_api_key_123456"
        mock_credentials.apisecret = "valid_api_secret_123456"

        assert self.middleware._has_valid_credentials("bitvavo", mock_credentials) is True

        # Invalid credentials (placeholders)
        mock_credentials.apikey = "BITVAVO API KEY"
        mock_credentials.apisecret = "BITVAVO API SECRET"

        assert self.middleware._has_valid_credentials("bitvavo", mock_credentials) is False

    def test_has_valid_credentials_ibkr(self):
        """Test _has_valid_credentials correctly validates IBKR credentials."""
        # Valid credentials
        mock_credentials = Mock()
        mock_credentials.access_token = "valid_access_token_123456"

        assert self.middleware._has_valid_credentials("ibkr", mock_credentials) is True

        # Invalid credentials (placeholder)
        mock_credentials.access_token = "IBKR ACCESS TOKEN"

        assert self.middleware._has_valid_credentials("ibkr", mock_credentials) is False

    def test_has_valid_credentials_unknown_broker(self):
        """Test _has_valid_credentials handles unknown brokers."""
        mock_credentials = Mock()

        # For unknown brokers, assume valid if credentials exist
        assert self.middleware._has_valid_credentials("unknown", mock_credentials) is True
        assert self.middleware._has_valid_credentials("unknown", None) is False
