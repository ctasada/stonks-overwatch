"""
Unit tests for refactored DeGiroAuthMiddleware.

This module tests the refactored DEGIRO-specific middleware that handles
DEGIRO connection checking, TOTP, and in-app authentication flows.
Note: General authentication and URL routing is now handled by AuthenticationMiddleware.
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

    def test_middleware_allows_authenticated_user(self):
        """Test middleware allows authenticated users to proceed when DEGIRO checks pass."""
        # Mock authentication service to return successful DEGIRO connection
        self.mock_auth_service.is_broker_enabled.return_value = True
        self.mock_auth_service.is_offline_mode.return_value = False
        self.mock_auth_service.should_check_connection.return_value = True
        self.mock_auth_service.check_broker_connection.return_value = AuthenticationResponse(
            result=AuthenticationResult.SUCCESS, session_id="test_session"
        )

        response = self.middleware(self.request)

        assert response == self.get_response.return_value
        self.mock_auth_service.check_broker_connection.assert_called_once_with(self.request)

    @patch("stonks_overwatch.middleware.degiro_auth.redirect")
    def test_middleware_redirects_on_degiro_failure(self, mock_redirect):
        """Test middleware redirects when DEGIRO authentication fails."""
        mock_redirect_response = Mock()
        mock_redirect.return_value = mock_redirect_response

        # Mock authentication service to return authentication failure
        self.mock_auth_service.is_broker_enabled.return_value = True
        self.mock_auth_service.is_offline_mode.return_value = False
        self.mock_auth_service.should_check_connection.return_value = True
        self.mock_auth_service.check_broker_connection.return_value = AuthenticationResponse(
            result=AuthenticationResult.INVALID_CREDENTIALS, message="Invalid credentials"
        )

        response = self.middleware(self.request)

        assert response == mock_redirect_response
        mock_redirect.assert_called_once_with("login")
        self.mock_auth_service.logout_user.assert_called_once_with(self.request)

    def test_middleware_skips_check_when_degiro_disabled(self):
        """Test middleware skips DEGIRO checks when DEGIRO is disabled."""
        # Mock authentication service to return DEGIRO disabled
        self.mock_auth_service.is_broker_enabled.return_value = False

        response = self.middleware(self.request)

        assert response == self.get_response.return_value
        # Should not check connection when DEGIRO is disabled
        self.mock_auth_service.should_check_connection.assert_not_called()

    def test_middleware_skips_check_in_offline_mode(self):
        """Test middleware skips DEGIRO checks in offline mode."""
        # Mock authentication service for offline mode
        self.mock_auth_service.is_broker_enabled.return_value = True
        self.mock_auth_service.is_offline_mode.return_value = True

        response = self.middleware(self.request)

        assert response == self.get_response.return_value
        # Should not check connection in offline mode
        self.mock_auth_service.should_check_connection.assert_not_called()

    @patch("stonks_overwatch.middleware.degiro_auth.redirect")
    def test_middleware_handles_totp_requirement(self, mock_redirect):
        """Test middleware handles TOTP requirement gracefully."""
        mock_redirect_response = Mock()
        mock_redirect.return_value = mock_redirect_response

        # Mock authentication service to return TOTP required
        self.mock_auth_service.is_broker_enabled.return_value = True
        self.mock_auth_service.is_offline_mode.return_value = False
        self.mock_auth_service.should_check_connection.return_value = True
        self.mock_auth_service.check_broker_connection.return_value = AuthenticationResponse(
            result=AuthenticationResult.TOTP_REQUIRED
        )

        response = self.middleware(self.request)

        assert response == mock_redirect_response
        mock_redirect.assert_called_once_with("login")
        # Should preserve session for TOTP flow
        self.mock_auth_service.logout_user.assert_not_called()
        self.mock_auth_service.session_manager.set_totp_required.assert_called_once_with(self.request, True)

    @patch("stonks_overwatch.middleware.degiro_auth.redirect")
    def test_middleware_handles_in_app_auth_requirement(self, mock_redirect):
        """Test middleware handles in-app authentication requirement."""
        mock_redirect_response = Mock()
        mock_redirect.return_value = mock_redirect_response

        # Mock authentication service to return in-app auth required
        self.mock_auth_service.is_broker_enabled.return_value = True
        self.mock_auth_service.is_offline_mode.return_value = False
        self.mock_auth_service.should_check_connection.return_value = True
        self.mock_auth_service.check_broker_connection.return_value = AuthenticationResponse(
            result=AuthenticationResult.IN_APP_AUTHENTICATION_REQUIRED
        )

        response = self.middleware(self.request)

        assert response == mock_redirect_response
        mock_redirect.assert_called_once_with("login")
        # Should preserve session for in-app auth flow
        self.mock_auth_service.logout_user.assert_not_called()
        self.mock_auth_service.session_manager.set_in_app_auth_required.assert_called_once_with(self.request, True)

    def test_middleware_skips_check_when_not_needed(self):
        """Test middleware skips check when connection check is not needed."""
        # Mock authentication service to indicate check not needed
        self.mock_auth_service.is_broker_enabled.return_value = True
        self.mock_auth_service.is_offline_mode.return_value = False
        self.mock_auth_service.should_check_connection.return_value = False

        response = self.middleware(self.request)

        assert response == self.get_response.return_value
        # Should not check connection when not needed
        self.mock_auth_service.check_broker_connection.assert_not_called()

    def test_middleware_handles_exceptions_gracefully(self):
        """Test middleware handles exceptions in authentication service gracefully."""
        # Mock authentication service to raise exception
        self.mock_auth_service.is_broker_enabled.side_effect = Exception("Test exception")

        response = self.middleware(self.request)

        # Should proceed despite exception (logged but not blocking)
        assert response == self.get_response.return_value
