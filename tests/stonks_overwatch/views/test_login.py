"""
Unit tests for refactored Login view.

This module tests the refactored login view to ensure it maintains
the same behavior while using AuthenticationService.
"""

from django.contrib.sessions.backends.db import SessionStore

from stonks_overwatch.core.interfaces.authentication_service import AuthenticationResponse, AuthenticationResult
from stonks_overwatch.views.login import Login

import pytest
from django.test import RequestFactory, TestCase
from unittest.mock import Mock, patch


@pytest.mark.django_db
class TestLoginViewRefactored(TestCase):
    """Test cases for refactored Login view."""

    @patch("stonks_overwatch.views.login.get_authentication_service")
    def setUp(self, mock_get_auth_service):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.mock_auth_service = Mock()
        mock_get_auth_service.return_value = self.mock_auth_service

        self.view = Login()
        self.view.setup(request=Mock())
        # The auth_service should now be set automatically via the locator
        self.session = SessionStore()

    def test_get_authenticated_user_shows_loading(self):
        """Test GET request for authenticated user shows loading state."""
        request = self.factory.get("/login/")
        request.session = self.session

        # Mock authenticated user
        self.mock_auth_service.session_manager.is_totp_required.return_value = False
        self.mock_auth_service.session_manager.is_in_app_auth_required.return_value = False
        self.mock_auth_service.is_user_authenticated.return_value = True

        response = self.view.get(request)

        assert response.status_code == 200
        # Check response content contains loading spinner
        content = response.content.decode("utf-8")
        assert "Loading..." in content or "spinner-border" in content  # Check for loading element

    def test_get_unauthenticated_user_normal_state(self):
        """Test GET request for unauthenticated user shows normal state."""
        request = self.factory.get("/login/")
        request.session = self.session

        # Mock unauthenticated user
        self.mock_auth_service.session_manager.is_totp_required.return_value = False
        self.mock_auth_service.session_manager.is_in_app_auth_required.return_value = False
        self.mock_auth_service.is_user_authenticated.return_value = False

        response = self.view.get(request)

        assert response.status_code == 200
        # Check response content - should show normal login form
        content = response.content.decode("utf-8")
        assert "username" in content.lower() and "password" in content.lower()  # Normal login form

    def test_get_totp_required_shows_otp(self):
        """Test GET request when TOTP is required shows OTP form."""
        request = self.factory.get("/login/")
        request.session = self.session

        # Mock TOTP required
        self.mock_auth_service.session_manager.is_totp_required.return_value = True
        self.mock_auth_service.session_manager.is_in_app_auth_required.return_value = False
        self.mock_auth_service.is_user_authenticated.return_value = False

        response = self.view.get(request)

        assert response.status_code == 200
        # Check response content - should show OTP form
        content = response.content.decode("utf-8")
        assert "2fa" in content.lower() or "otp" in content.lower()  # OTP form should be visible

    @patch("stonks_overwatch.jobs.jobs_scheduler.JobsScheduler.update_portfolio")
    def test_post_update_portfolio_redirects(self, mock_update):
        """Test POST request with update_portfolio redirects to dashboard."""
        request = self.factory.post("/login/", {"update_portfolio": "true"})
        request.session = self.session

        response = self.view.post(request)

        assert response.status_code == 302
        assert response.url == "/dashboard"
        mock_update.assert_called_once()

    def test_post_successful_authentication_shows_loading(self):
        """Test POST request with successful authentication shows loading."""
        request = self.factory.post("/login/", {"username": "testuser", "password": "testpass"})
        request.session = self.session

        # Mock degiro_config.get_credentials.username
        degiro_config = Mock()
        degiro_config.get_credentials.username = "degiro_user"
        self.mock_auth_service.degiro_config = degiro_config

        # Mock successful authentication
        auth_response = AuthenticationResponse(result=AuthenticationResult.SUCCESS, session_id="test_session")
        self.mock_auth_service.authenticate_user.return_value = auth_response

        # Logic for remember_me - defaults to False when not provided
        remember_me = False

        response = self.view.post(request)

        assert response.status_code == 200
        # Check response content contains loading indicator
        content = response.content.decode("utf-8")
        assert "Loading..." in content or "spinner-border" in content
        self.mock_auth_service.authenticate_user.assert_called_once_with(
            request, "testuser", "testpass", None, remember_me
        )

    def test_post_totp_required_shows_otp_form(self):
        """Test POST request requiring TOTP shows OTP form."""
        request = self.factory.post("/login/", {"username": "testuser", "password": "testpass"})
        request.session = self.session

        # Mock TOTP required
        auth_response = AuthenticationResponse(result=AuthenticationResult.TOTP_REQUIRED, requires_totp=True)
        self.mock_auth_service.authenticate_user.return_value = auth_response

        response = self.view.post(request)

        assert response.status_code == 200
        # Check response content shows OTP form
        content = response.content.decode("utf-8")
        assert "2fa" in content.lower() or "otp" in content.lower()

    def test_post_totp_authentication_success(self):
        """Test POST request with TOTP code for successful authentication."""
        request = self.factory.post("/login/", {"2fa_code": "123456"})
        request.session = self.session

        # Mock successful TOTP authentication
        auth_response = AuthenticationResponse(result=AuthenticationResult.SUCCESS, session_id="test_session")
        self.mock_auth_service.handle_totp_authentication.return_value = auth_response

        response = self.view.post(request)

        assert response.status_code == 200
        # Check response content shows loading indicator after successful TOTP
        content = response.content.decode("utf-8")
        assert "Loading..." in content or "spinner-border" in content
        self.mock_auth_service.handle_totp_authentication.assert_called_once_with(request, 123456)

    def test_post_invalid_credentials_shows_error(self):
        """Test POST request with invalid credentials shows error."""
        request = self.factory.post("/login/", {"username": "testuser", "password": "wrongpass"})
        request.session = self.session

        # Mock invalid credentials
        auth_response = AuthenticationResponse(
            result=AuthenticationResult.INVALID_CREDENTIALS, message="Invalid username or password"
        )
        self.mock_auth_service.authenticate_user.return_value = auth_response

        with patch("django.contrib.messages.error") as mock_messages:
            response = self.view.post(request)

        assert response.status_code == 200
        # Check that error is displayed (not loading or OTP)
        content = response.content.decode("utf-8")
        assert "loading" not in content.lower() or 'style="display: none"' in content
        mock_messages.assert_called_once_with(request, "Invalid username or password")

    def test_post_missing_credentials_shows_error(self):
        """Test POST request with missing credentials shows error."""
        request = self.factory.post("/login/", {})
        request.session = self.session

        with patch("django.contrib.messages.error") as mock_messages:
            response = self.view.post(request)

        assert response.status_code == 400
        # Check that normal login form is shown with error (not OTP form)
        content = response.content.decode("utf-8")
        assert "username" in content.lower() and "password" in content.lower()
        mock_messages.assert_called_once_with(request, "Username and password are required.")

    def test_post_maintenance_mode_shows_error(self):
        """Test POST request during maintenance mode shows error."""
        request = self.factory.post("/login/", {"username": "testuser", "password": "testpass"})
        request.session = self.session

        # Mock maintenance mode
        auth_response = AuthenticationResponse(
            result=AuthenticationResult.MAINTENANCE_MODE, message="System is under maintenance"
        )
        self.mock_auth_service.authenticate_user.return_value = auth_response

        with patch("django.contrib.messages.error") as mock_messages:
            response = self.view.post(request)

        assert response.status_code == 200
        mock_messages.assert_called_once_with(request, "System is under maintenance")

    def test_post_connection_error_shows_error(self):
        """Test POST request with connection error shows error."""
        request = self.factory.post("/login/", {"username": "testuser", "password": "testpass"})
        request.session = self.session

        # Mock connection error
        auth_response = AuthenticationResponse(
            result=AuthenticationResult.CONNECTION_ERROR, message="Network connection failed"
        )
        self.mock_auth_service.authenticate_user.return_value = auth_response

        with patch("django.contrib.messages.error") as mock_messages:
            response = self.view.post(request)

        assert response.status_code == 200
        mock_messages.assert_called_once_with(
            request, "Unable to connect to the authentication service. Please check your connection and try again."
        )

    def test_post_unknown_error_shows_generic_error(self):
        """Test POST request with unknown error shows generic error."""
        request = self.factory.post("/login/", {"username": "testuser", "password": "testpass"})
        request.session = self.session

        # Mock unknown error
        auth_response = AuthenticationResponse(
            result=AuthenticationResult.UNKNOWN_ERROR, message="Unexpected error occurred"
        )
        self.mock_auth_service.authenticate_user.return_value = auth_response

        with patch("django.contrib.messages.error") as mock_messages:
            response = self.view.post(request)

        assert response.status_code == 200
        mock_messages.assert_called_once_with(request, "Unexpected error occurred")

    def test_extract_credentials_valid_data(self):
        """Test _extract_credentials with valid form data."""
        request = self.factory.post(
            "/login/", {"username": "testuser", "password": "testpass", "2fa_code": "123456", "remember_me": "true"}
        )

        credentials = self.view._extract_credentials(request)

        assert credentials is not None
        assert credentials["username"] == "testuser"
        assert credentials["password"] == "testpass"
        assert credentials["one_time_password"] == 123456
        assert credentials["remember_me"] is True

    def test_extract_credentials_invalid_otp(self):
        """Test _extract_credentials with invalid OTP converts to None."""
        request = self.factory.post("/login/", {"username": "testuser", "password": "testpass", "2fa_code": "invalid"})

        credentials = self.view._extract_credentials(request)

        assert credentials is not None
        assert credentials["one_time_password"] is None

    def test_extract_credentials_missing_required(self):
        """Test _extract_credentials with missing required fields returns None."""
        request = self.factory.post("/login/", {"password": "testpass"})

        credentials = self.view._extract_credentials(request)

        assert credentials is None

    def test_perform_authentication_regular_login(self):
        """Test _perform_authentication for regular login."""
        request = self.factory.post("/login/")
        credentials = {"username": "testuser", "password": "testpass", "one_time_password": None, "remember_me": False}

        expected_response = AuthenticationResponse(result=AuthenticationResult.SUCCESS)
        self.mock_auth_service.authenticate_user.return_value = expected_response

        result = self.view._perform_authentication(request, credentials)

        assert result == expected_response
        self.mock_auth_service.authenticate_user.assert_called_once_with(request, "testuser", "testpass", None, False)

    def test_perform_authentication_totp_flow(self):
        """Test _perform_authentication for TOTP flow."""
        request = self.factory.post("/login/")
        credentials = {
            "username": "testuser",
            "password": "testpass",
            "one_time_password": 123456,
            "remember_me": False,
        }

        expected_response = AuthenticationResponse(result=AuthenticationResult.SUCCESS)
        self.mock_auth_service.handle_totp_authentication.return_value = expected_response

        result = self.view._perform_authentication(request, credentials)

        assert result == expected_response
        self.mock_auth_service.handle_totp_authentication.assert_called_once_with(request, 123456)

    def test_handle_auth_result_success(self):
        """Test _handle_auth_result for successful authentication."""
        request = self.factory.post("/login/")
        auth_result = AuthenticationResponse(result=AuthenticationResult.SUCCESS)

        show_otp, show_loading, show_in_app_auth = self.view._handle_auth_result(request, auth_result)

        assert show_otp is False
        assert show_loading is True
        assert show_in_app_auth is False

    def test_handle_auth_result_totp_required(self):
        """Test _handle_auth_result for TOTP required."""
        request = self.factory.post("/login/")
        auth_result = AuthenticationResponse(result=AuthenticationResult.TOTP_REQUIRED)

        show_otp, show_loading, show_in_app_auth = self.view._handle_auth_result(request, auth_result)

        assert show_otp is True
        assert show_loading is False
        assert show_in_app_auth is False

    def test_get_in_app_auth_required_shows_dialog(self):
        """Test GET request when in-app authentication is required shows dialog."""
        request = self.factory.get("/login/")
        request.session = self.session

        # Mock in-app auth required
        self.mock_auth_service.session_manager.is_totp_required.return_value = False
        self.mock_auth_service.session_manager.is_in_app_auth_required.return_value = True
        self.mock_auth_service.is_user_authenticated.return_value = False

        response = self.view.get(request)

        assert response.status_code == 200
        # Check response content - should show in-app auth dialog
        content = response.content.decode("utf-8")
        assert "open the degiro app" in content.lower() or "service desk" in content.lower()

    def test_handle_auth_result_in_app_auth_required(self):
        """Test _handle_auth_result for in-app authentication required."""
        request = self.factory.post("/login/")
        auth_result = AuthenticationResponse(result=AuthenticationResult.IN_APP_AUTHENTICATION_REQUIRED)

        show_otp, show_loading, show_in_app_auth = self.view._handle_auth_result(request, auth_result)

        assert show_otp is False
        assert show_loading is False
        assert show_in_app_auth is True

    def test_post_account_blocked_shows_error(self):
        """Test POST request with account blocked shows error message."""
        request = self.factory.post("/login/", {"username": "testuser", "password": "testpass"})
        request.session = self.session

        # Mock account blocked
        auth_response = AuthenticationResponse(
            result=AuthenticationResult.ACCOUNT_BLOCKED,
            message="Your account has been blocked because the maximum of login attempts has been exceeded",
        )
        self.mock_auth_service.authenticate_user.return_value = auth_response

        with patch("django.contrib.messages.error") as mock_messages:
            response = self.view.post(request)

        assert response.status_code == 200
        # Check that the account blocked message is shown
        mock_messages.assert_called_once()
        call_args = mock_messages.call_args[0]
        assert "blocked" in call_args[1].lower()
        assert "service desk" in call_args[1].lower()

    def test_render_login_error(self):
        """Test _render_login_error method."""
        request = self.factory.post("/login/")

        with patch("django.contrib.messages.error") as mock_messages:
            response = self.view._render_login_error(request, "Test error message")

        assert response.status_code == 400
        # Check that the response is rendered (contains HTML structure)
        content = response.content.decode("utf-8")
        assert "<html>" in content or "<!DOCTYPE" in content  # Basic HTML structure check
        mock_messages.assert_called_once_with(request, "Test error message")
