"""
Unit tests for AuthenticationSessionManager.

This module contains comprehensive tests for the authentication session manager,
including session state management, credential storage, and error handling.
"""

from django.http import HttpRequest

from stonks_overwatch.config.degiro import DegiroCredentials
from stonks_overwatch.services.utilities.authentication_session_manager import AuthenticationSessionManager

from django.test import TestCase
from unittest.mock import Mock, patch


class TestAuthenticationSessionManager(TestCase):
    """Test cases for AuthenticationSessionManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.session_manager = AuthenticationSessionManager()
        self.request = self._create_mock_request()

    def _create_mock_request(self):
        """Create a mock request with session."""
        request = Mock(spec=HttpRequest)

        # Create a proper session mock that behaves like Django's session
        class MockSession(dict):
            def __init__(self):
                super().__init__()
                self.modified = False

            def __setitem__(self, key, value):
                super().__setitem__(key, value)
                self.modified = True

            def __delitem__(self, key):
                super().__delitem__(key)
                self.modified = True

            def save(self):
                pass

            def flush(self):
                self.clear()
                self.modified = True

        request.session = MockSession()
        return request

    def test_is_authenticated_with_valid_session(self):
        """Test is_authenticated returns True for valid authenticated session."""
        # Setup valid session
        self.request.session[AuthenticationSessionManager.SESSION_IS_AUTHENTICATED] = True
        self.request.session[AuthenticationSessionManager.SESSION_ID_KEY] = "test_session_123"

        result = self.session_manager.is_authenticated(self.request)

        assert result is True

    def test_is_authenticated_with_missing_authentication_flag(self):
        """Test is_authenticated returns False when authentication flag is missing."""
        self.request.session[AuthenticationSessionManager.SESSION_ID_KEY] = "test_session_123"

        result = self.session_manager.is_authenticated(self.request)

        assert result is False

    def test_is_authenticated_with_false_authentication_flag(self):
        """Test is_authenticated returns False when authentication flag is False."""
        self.request.session[AuthenticationSessionManager.SESSION_IS_AUTHENTICATED] = False
        self.request.session[AuthenticationSessionManager.SESSION_ID_KEY] = "test_session_123"

        result = self.session_manager.is_authenticated(self.request)

        assert result is False

    def test_is_authenticated_with_missing_session_id(self):
        """Test is_authenticated returns False when session ID is missing."""
        self.request.session[AuthenticationSessionManager.SESSION_IS_AUTHENTICATED] = True

        result = self.session_manager.is_authenticated(self.request)

        assert result is False

    def test_is_authenticated_with_empty_session_id(self):
        """Test is_authenticated returns False when session ID is empty."""
        self.request.session[AuthenticationSessionManager.SESSION_IS_AUTHENTICATED] = True
        self.request.session[AuthenticationSessionManager.SESSION_ID_KEY] = ""

        result = self.session_manager.is_authenticated(self.request)

        assert result is False

    def test_is_authenticated_with_exception(self):
        """Test is_authenticated handles exceptions gracefully."""

        # Create a custom mock session that raises on .get()
        class ExceptionSession:
            def get(self, key, default=None):
                raise Exception("Session error")

        self.request.session = ExceptionSession()

        result = self.session_manager.is_authenticated(self.request)

        assert result is False
        # Note: We can't easily mock the logger since it's already instantiated,
        # but we can verify the exception was handled gracefully by checking the return value

    def test_set_authenticated_true(self):
        """Test set_authenticated sets authentication status to True."""
        self.session_manager.set_authenticated(self.request, True)

        assert self.request.session[AuthenticationSessionManager.SESSION_IS_AUTHENTICATED] is True
        assert hasattr(self.request.session, "modified")

    def test_set_authenticated_false(self):
        """Test set_authenticated sets authentication status to False."""
        self.session_manager.set_authenticated(self.request, False)

        assert self.request.session[AuthenticationSessionManager.SESSION_IS_AUTHENTICATED] is False
        assert hasattr(self.request.session, "modified")

    def test_set_authenticated_with_exception(self):
        """Test set_authenticated handles exceptions gracefully."""

        # Create a custom mock session that raises on assignment
        class ExceptionSession:
            def __setitem__(self, key, value):
                raise Exception("Session error")

            def __contains__(self, key):
                return False

        self.request.session = ExceptionSession()

        # Should not raise exception - error is handled gracefully
        self.session_manager.set_authenticated(self.request, True)

    def test_get_session_id_exists(self):
        """Test get_session_id returns existing session ID."""
        test_session_id = "test_session_123"
        self.request.session[AuthenticationSessionManager.SESSION_ID_KEY] = test_session_id

        result = self.session_manager.get_session_id(self.request)

        assert result == test_session_id

    def test_get_session_id_not_exists(self):
        """Test get_session_id returns None when session ID doesn't exist."""
        result = self.session_manager.get_session_id(self.request)

        assert result is None

    def test_set_session_id(self):
        """Test set_session_id stores session ID."""
        test_session_id = "test_session_123"

        self.session_manager.set_session_id(self.request, test_session_id)

        assert self.request.session[AuthenticationSessionManager.SESSION_ID_KEY] == test_session_id
        assert hasattr(self.request.session, "modified")

    def test_get_credentials_exists(self):
        """Test get_credentials returns existing credentials."""
        credentials_data = {"username": "testuser", "password": "testpass", "remember_me": True}
        self.request.session[AuthenticationSessionManager.SESSION_CREDENTIALS_KEY] = credentials_data

        result = self.session_manager.get_credentials(self.request)

        assert isinstance(result, DegiroCredentials)
        assert result.username == "testuser"
        assert result.password == "testpass"
        assert result.remember_me is True

    def test_get_credentials_not_exists(self):
        """Test get_credentials returns None when credentials don't exist."""
        result = self.session_manager.get_credentials(self.request)

        assert result is None

    @patch("stonks_overwatch.services.utilities.authentication_session_manager.DegiroCredentials")
    def test_get_credentials_with_exception(self, mock_credentials):
        """Test get_credentials handles exceptions gracefully."""
        mock_credentials.from_dict.side_effect = Exception("Credential error")
        self.request.session[AuthenticationSessionManager.SESSION_CREDENTIALS_KEY] = {"username": "test"}

        result = self.session_manager.get_credentials(self.request)

        assert result is None
        # Exception is handled gracefully and None is returned

    def test_store_credentials(self):
        """Test store_credentials stores credentials in session."""
        username = "testuser"
        password = "testpass"
        remember_me = True

        self.session_manager.store_credentials(
            request=self.request, username=username, password=password, remember_me=remember_me
        )

        stored_credentials = self.request.session[AuthenticationSessionManager.SESSION_CREDENTIALS_KEY]
        assert stored_credentials["username"] == username
        assert stored_credentials["password"] == password
        assert stored_credentials["remember_me"] == remember_me
        assert hasattr(self.request.session, "modified")

    def test_store_credentials_default_remember_me(self):
        """Test store_credentials with default remember_me value."""
        username = "testuser"
        password = "testpass"

        self.session_manager.store_credentials(self.request, username, password)

        stored_credentials = self.request.session[AuthenticationSessionManager.SESSION_CREDENTIALS_KEY]
        assert stored_credentials["remember_me"] is False

    def test_set_totp_required_true(self):
        """Test set_totp_required sets TOTP requirement to True."""
        self.session_manager.set_totp_required(self.request, True)

        assert self.request.session[AuthenticationSessionManager.SESSION_SHOW_OTP_KEY] is True
        assert hasattr(self.request.session, "modified")

    def test_set_totp_required_false(self):
        """Test set_totp_required sets TOTP requirement to False."""
        self.session_manager.set_totp_required(self.request, False)

        assert self.request.session[AuthenticationSessionManager.SESSION_SHOW_OTP_KEY] is False
        assert hasattr(self.request.session, "modified")

    def test_set_totp_required_default(self):
        """Test set_totp_required with default value (True)."""
        self.session_manager.set_totp_required(self.request)

        assert self.request.session[AuthenticationSessionManager.SESSION_SHOW_OTP_KEY] is True

    def test_is_totp_required_true(self):
        """Test is_totp_required returns True when TOTP is required."""
        self.request.session[AuthenticationSessionManager.SESSION_SHOW_OTP_KEY] = True

        result = self.session_manager.is_totp_required(self.request)

        assert result is True

    def test_is_totp_required_false(self):
        """Test is_totp_required returns False when TOTP is not required."""
        self.request.session[AuthenticationSessionManager.SESSION_SHOW_OTP_KEY] = False

        result = self.session_manager.is_totp_required(self.request)

        assert result is False

    def test_is_totp_required_default(self):
        """Test is_totp_required returns False when key doesn't exist."""
        result = self.session_manager.is_totp_required(self.request)

        assert result is False

    def test_clear_session(self):
        """Test clear_session removes all authentication data."""
        # Setup session with all authentication data
        self.request.session[AuthenticationSessionManager.SESSION_IS_AUTHENTICATED] = True
        self.request.session[AuthenticationSessionManager.SESSION_ID_KEY] = "test_session"
        self.request.session[AuthenticationSessionManager.SESSION_CREDENTIALS_KEY] = {"username": "test"}
        self.request.session[AuthenticationSessionManager.SESSION_SHOW_OTP_KEY] = True
        self.request.session["other_data"] = "should_remain"

        self.session_manager.clear_session(self.request)

        # Authentication data should be removed
        assert AuthenticationSessionManager.SESSION_IS_AUTHENTICATED not in self.request.session
        assert AuthenticationSessionManager.SESSION_ID_KEY not in self.request.session
        assert AuthenticationSessionManager.SESSION_CREDENTIALS_KEY not in self.request.session
        assert AuthenticationSessionManager.SESSION_SHOW_OTP_KEY not in self.request.session

        # Other data should remain
        assert self.request.session["other_data"] == "should_remain"
        assert hasattr(self.request.session, "modified")

    def test_get_session_data_complete(self):
        """Test get_session_data returns complete session information."""
        # Setup session with all data
        self.request.session[AuthenticationSessionManager.SESSION_IS_AUTHENTICATED] = True
        self.request.session[AuthenticationSessionManager.SESSION_ID_KEY] = "test_session_123456789"
        self.request.session[AuthenticationSessionManager.SESSION_CREDENTIALS_KEY] = {
            "username": "testuser",
            "password": "secret123",
            "remember_me": True,
        }
        self.request.session[AuthenticationSessionManager.SESSION_SHOW_OTP_KEY] = True

        result = self.session_manager.get_session_data(self.request)

        assert result["is_authenticated"] is True
        assert result["session_id"] == "test_ses..."  # Should be masked
        assert result["credentials"]["username"] == "testuser"
        assert result["credentials"]["password"] == "***MASKED***"  # Should be masked
        assert result["credentials"]["remember_me"] is True
        assert result["totp_required"] is True

    def test_get_session_data_minimal(self):
        """Test get_session_data with minimal session data."""
        result = self.session_manager.get_session_data(self.request)

        assert result["is_authenticated"] is False
        assert result["session_id"] is None
        assert result["credentials"] is None
        assert result["totp_required"] is False

    def test_get_session_data_with_short_session_id(self):
        """Test get_session_data handles short session IDs correctly."""
        self.request.session[AuthenticationSessionManager.SESSION_ID_KEY] = "short"

        result = self.session_manager.get_session_data(self.request)

        assert result["session_id"] == "short"  # Should not be masked

    def test_get_session_data_with_exception(self):
        """Test get_session_data handles exceptions gracefully."""

        class ExceptionSession:
            def get(self, key, default=None):
                raise Exception("Session error")

        self.request.session = ExceptionSession()

        result = self.session_manager.get_session_data(self.request)

        assert "error" in result
        # Exception is handled gracefully and error info is returned

    def test_dependency_injection_with_config(self):
        """Test that AuthenticationSessionManager works with dependency injection."""
        mock_config = Mock()
        session_manager = AuthenticationSessionManager(config=mock_config)

        assert session_manager.config == mock_config
        assert session_manager.is_dependency_injection_enabled() is True

    def test_dependency_injection_without_config(self):
        """Test that AuthenticationSessionManager works without dependency injection."""
        session_manager = AuthenticationSessionManager()

        assert session_manager.config is not None  # Should use global config
        assert session_manager.is_dependency_injection_enabled() is False
