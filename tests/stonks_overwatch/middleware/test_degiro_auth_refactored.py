"""
Unit tests for refactored DeGiroAuthMiddleware.

This module tests the refactored middleware to ensure it maintains
the same behavior while using AuthenticationService.
"""

from django.http import HttpRequest, HttpResponse

from stonks_overwatch.core.interfaces.authentication_service import AuthenticationResponse, AuthenticationResult
from stonks_overwatch.middleware.degiro_auth import DeGiroAuthMiddleware

from django.test import TestCase
from unittest.mock import Mock, patch


class TestDeGiroAuthMiddlewareRefactored(TestCase):
    """Test cases for refactored DeGiroAuthMiddleware."""

    @patch("stonks_overwatch.middleware.degiro_auth.get_authentication_service")
    def setUp(self, mock_get_auth_service):
        """Set up test fixtures."""
        self.get_response = Mock(return_value=HttpResponse())
        self.mock_auth_service = Mock()
        mock_get_auth_service.return_value = self.mock_auth_service
        self.middleware = DeGiroAuthMiddleware(self.get_response)
        self.request = self._create_mock_request()

    def _create_mock_request(self):
        """Create a mock request with session."""
        request = Mock(spec=HttpRequest)
        request.session = {}
        request.path_info = "/dashboard/"
        return request

    @patch("stonks_overwatch.middleware.degiro_auth.resolve")
    def test_middleware_allows_authenticated_user(self, mock_resolve):
        """Test middleware allows authenticated users to proceed."""
        mock_resolve.return_value.url_name = "dashboard"

        # Mock authentication service to return authenticated
        self.mock_auth_service.is_degiro_enabled.return_value = True
        self.mock_auth_service.is_offline_mode.return_value = False
        self.mock_auth_service.should_check_connection.return_value = True
        self.mock_auth_service.check_degiro_connection.return_value = AuthenticationResponse(
            result=AuthenticationResult.SUCCESS, session_id="test_session"
        )
        self.mock_auth_service.is_user_authenticated.return_value = True
        self.mock_auth_service.is_maintenance_mode_allowed.return_value = True

        response = self.middleware(self.request)

        # Should proceed to the actual view
        assert response == self.get_response.return_value
        self.get_response.assert_called_once_with(self.request)

    @patch("stonks_overwatch.middleware.degiro_auth.resolve")
    @patch("stonks_overwatch.middleware.degiro_auth.redirect")
    def test_middleware_redirects_unauthenticated_user(self, mock_redirect, mock_resolve):
        """Test middleware redirects unauthenticated users to login."""
        mock_resolve.return_value.url_name = "dashboard"
        mock_redirect_response = Mock()
        mock_redirect.return_value = mock_redirect_response

        # Mock authentication service to return not authenticated
        self.mock_auth_service.is_degiro_enabled.return_value = True
        self.mock_auth_service.is_offline_mode.return_value = False
        self.mock_auth_service.should_check_connection.return_value = False
        self.mock_auth_service.is_user_authenticated.return_value = False
        self.mock_auth_service.is_maintenance_mode_allowed.return_value = False

        response = self.middleware(self.request)

        # Should redirect to login
        assert response == mock_redirect_response
        mock_redirect.assert_called_once_with("login")
        self.mock_auth_service.logout_user.assert_called_once_with(self.request)

    @patch("stonks_overwatch.middleware.degiro_auth.resolve")
    def test_middleware_allows_public_urls(self, mock_resolve):
        """Test middleware allows access to public URLs without authentication."""
        mock_resolve.return_value.url_name = "login"

        # Mock authentication service to return not authenticated
        self.mock_auth_service.is_degiro_enabled.return_value = True
        self.mock_auth_service.is_offline_mode.return_value = False
        self.mock_auth_service.should_check_connection.return_value = False
        self.mock_auth_service.is_user_authenticated.return_value = False

        response = self.middleware(self.request)

        # Should proceed to the actual view (login page)
        assert response == self.get_response.return_value
        self.get_response.assert_called_once_with(self.request)

    @patch("stonks_overwatch.middleware.degiro_auth.resolve")
    def test_middleware_handles_degiro_disabled(self, mock_resolve):
        """Test middleware when DeGiro is disabled."""
        mock_resolve.return_value.url_name = "dashboard"

        # Mock authentication service to return DeGiro disabled
        self.mock_auth_service.is_degiro_enabled.return_value = False
        self.mock_auth_service.is_user_authenticated.return_value = True
        self.mock_auth_service.is_maintenance_mode_allowed.return_value = True

        response = self.middleware(self.request)

        # Should proceed without connection checks
        assert response == self.get_response.return_value
        self.mock_auth_service.should_check_connection.assert_not_called()

    @patch("stonks_overwatch.middleware.degiro_auth.resolve")
    def test_middleware_handles_offline_mode(self, mock_resolve):
        """Test middleware when DeGiro is in offline mode."""
        mock_resolve.return_value.url_name = "dashboard"

        # Mock authentication service for offline mode
        self.mock_auth_service.is_degiro_enabled.return_value = True
        self.mock_auth_service.is_offline_mode.return_value = True
        self.mock_auth_service.is_user_authenticated.return_value = True
        self.mock_auth_service.is_maintenance_mode_allowed.return_value = True

        response = self.middleware(self.request)

        # Should proceed without connection checks
        assert response == self.get_response.return_value
        self.mock_auth_service.should_check_connection.assert_not_called()

    @patch("stonks_overwatch.middleware.degiro_auth.resolve")
    @patch("stonks_overwatch.middleware.degiro_auth.redirect")
    def test_middleware_handles_totp_requirement(self, mock_redirect, mock_resolve):
        """Test middleware handles TOTP requirement gracefully."""
        mock_resolve.return_value.url_name = "dashboard"
        mock_redirect_response = Mock()
        mock_redirect.return_value = mock_redirect_response

        # Mock authentication service to return TOTP required
        self.mock_auth_service.is_degiro_enabled.return_value = True
        self.mock_auth_service.is_offline_mode.return_value = False
        self.mock_auth_service.should_check_connection.return_value = True
        self.mock_auth_service.check_degiro_connection.return_value = AuthenticationResponse(
            result=AuthenticationResult.TOTP_REQUIRED, requires_totp=True
        )
        self.mock_auth_service.is_user_authenticated.return_value = True
        self.mock_auth_service.is_maintenance_mode_allowed.return_value = True

        response = self.middleware(self.request)

        # Should redirect to login but preserve session for TOTP flow
        assert response == mock_redirect_response
        mock_redirect.assert_called_once_with("login")
        # Should NOT call logout_user (session preserved for TOTP)
        self.mock_auth_service.logout_user.assert_not_called()
        # Should set TOTP required flag in session
        self.mock_auth_service.session_manager.set_totp_required.assert_called_once_with(self.request, True)

    @patch("stonks_overwatch.middleware.degiro_auth.resolve")
    @patch("stonks_overwatch.middleware.degiro_auth.redirect")
    def test_middleware_handles_connection_errors(self, mock_redirect, mock_resolve):
        """Test middleware handles connection errors gracefully."""
        mock_resolve.return_value.url_name = "dashboard"
        mock_redirect_response = Mock()
        mock_redirect.return_value = mock_redirect_response

        # Mock authentication service to return connection error
        self.mock_auth_service.is_degiro_enabled.return_value = True
        self.mock_auth_service.is_offline_mode.return_value = False
        self.mock_auth_service.should_check_connection.return_value = True
        self.mock_auth_service.check_degiro_connection.return_value = AuthenticationResponse(
            result=AuthenticationResult.CONNECTION_ERROR, message="Connection failed"
        )
        self.mock_auth_service.is_user_authenticated.return_value = True
        self.mock_auth_service.is_maintenance_mode_allowed.return_value = True

        response = self.middleware(self.request)

        # Should redirect to login due to connection error
        assert response == mock_redirect_response
        mock_redirect.assert_called_once_with("login")
        self.mock_auth_service.logout_user.assert_called_once_with(self.request)

    @patch("stonks_overwatch.middleware.degiro_auth.resolve")
    def test_middleware_allows_maintenance_mode_access(self, mock_resolve):
        """Test middleware allows access during maintenance mode when allowed."""
        mock_resolve.return_value.url_name = "dashboard"

        # Mock authentication service for maintenance mode with access allowed
        self.mock_auth_service.is_degiro_enabled.return_value = True
        self.mock_auth_service.is_offline_mode.return_value = False
        self.mock_auth_service.should_check_connection.return_value = False
        self.mock_auth_service.is_user_authenticated.return_value = True
        self.mock_auth_service.is_maintenance_mode_allowed.return_value = True

        response = self.middleware(self.request)

        # Should proceed (maintenance mode access is allowed)
        assert response == self.get_response.return_value

    @patch("stonks_overwatch.middleware.degiro_auth.resolve")
    def test_middleware_handles_exceptions_gracefully(self, mock_resolve):
        """Test middleware handles exceptions in authentication service gracefully."""
        mock_resolve.return_value.url_name = "dashboard"

        # Mock authentication service to raise exception
        self.mock_auth_service.is_degiro_enabled.side_effect = Exception("Service error")
        self.mock_auth_service.is_user_authenticated.return_value = True
        self.mock_auth_service.is_maintenance_mode_allowed.return_value = True

        response = self.middleware(self.request)

        # Should proceed despite exception (logged but not blocking)
        assert response == self.get_response.return_value

    def test_is_public_url_method(self):
        """Test _is_public_url method correctly identifies public URLs."""
        assert self.middleware._is_public_url("login") is True
        assert self.middleware._is_public_url("expired") is True
        assert self.middleware._is_public_url("dashboard") is False
        assert self.middleware._is_public_url(None) is False
