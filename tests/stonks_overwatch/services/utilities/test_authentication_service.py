"""
Unit tests for AuthenticationService.

This module contains comprehensive tests for the main authentication service
that orchestrates session management, credential handling, and DeGiro API operations.
"""

from degiro_connector.core.exceptions import DeGiroConnectionError, MaintenanceError
from django.http import HttpRequest

from stonks_overwatch.config.degiro import DegiroCredentials
from stonks_overwatch.core.interfaces.authentication_service import AuthenticationResponse, AuthenticationResult
from stonks_overwatch.services.utilities.authentication_service import AuthenticationService

import pytest
from django.test import TestCase
from unittest.mock import Mock, patch


@pytest.mark.django_db
class TestAuthenticationService(TestCase):
    """Test cases for AuthenticationService."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_session_manager = Mock()
        self.mock_credential_service = Mock()
        self.mock_degiro_service = Mock()

        self.auth_service = AuthenticationService(
            session_manager=self.mock_session_manager,
            credential_service=self.mock_credential_service,
            degiro_service=self.mock_degiro_service,
        )

        self.request = self._create_mock_request()

    def _create_mock_request(self):
        """Create a mock request with session."""
        request = Mock(spec=HttpRequest)
        request.session = {}
        return request

    def test_is_user_authenticated_valid(self):
        """Test is_user_authenticated returns True for valid authenticated user."""
        self.mock_session_manager.is_authenticated.return_value = True
        self.mock_session_manager.get_session_id.return_value = "test_session_123"

        result = self.auth_service.is_user_authenticated(self.request)

        assert result is True
        self.mock_session_manager.is_authenticated.assert_called_once_with(self.request)
        self.mock_session_manager.get_session_id.assert_called_once_with(self.request)

    def test_is_user_authenticated_not_authenticated(self):
        """Test is_user_authenticated returns False when not authenticated."""
        self.mock_session_manager.is_authenticated.return_value = False

        result = self.auth_service.is_user_authenticated(self.request)

        assert result is False
        self.mock_session_manager.is_authenticated.assert_called_once_with(self.request)

    def test_is_user_authenticated_no_session_id(self):
        """Test is_user_authenticated returns False when no session ID."""
        self.mock_session_manager.is_authenticated.return_value = True
        self.mock_session_manager.get_session_id.return_value = None

        result = self.auth_service.is_user_authenticated(self.request)

        assert result is False

    def test_is_user_authenticated_with_exception(self):
        """Test is_user_authenticated handles exceptions gracefully."""
        self.mock_session_manager.is_authenticated.side_effect = Exception("Session error")

        result = self.auth_service.is_user_authenticated(self.request)

        assert result is False
        # Exception is handled gracefully and False is returned

    def test_authenticate_user_success(self):
        """Test authenticate_user successful flow."""
        # Setup mocks
        credentials = DegiroCredentials("testuser", "testpass", remember_me=True)
        self.mock_credential_service.validate_credentials.return_value = True
        self.mock_degiro_service.get_session_id.return_value = "test_session_123"

        # Mock _get_effective_credentials and _authenticate_with_degiro
        with (
            patch.object(self.auth_service, "_get_effective_credentials") as mock_get_creds,
            patch.object(self.auth_service, "_authenticate_with_degiro") as mock_auth_degiro,
        ):
            mock_get_creds.return_value = credentials
            mock_auth_degiro.return_value = AuthenticationResponse(
                result=AuthenticationResult.SUCCESS, session_id="test_session_123"
            )

            result = self.auth_service.authenticate_user(self.request, "testuser", "testpass", remember_me=True)

            assert result.is_success
            assert result.session_id == "test_session_123"
            self.mock_session_manager.store_credentials.assert_called_once()
            self.mock_credential_service.store_credentials_in_database.assert_called_once()

    def test_authenticate_user_no_credentials(self):
        """Test authenticate_user when no credentials available."""
        with patch.object(self.auth_service, "_get_effective_credentials") as mock_get_creds:
            mock_get_creds.return_value = None

            result = self.auth_service.authenticate_user(self.request)

            assert result.result == AuthenticationResult.CONFIGURATION_ERROR
            assert "Authentication configuration error" in result.message

    def test_authenticate_user_invalid_credentials(self):
        """Test authenticate_user with invalid credential format."""
        credentials = DegiroCredentials("", "")
        self.mock_credential_service.validate_credentials.return_value = False

        with patch.object(self.auth_service, "_get_effective_credentials") as mock_get_creds:
            mock_get_creds.return_value = credentials

            result = self.auth_service.authenticate_user(self.request)

            assert result.result == AuthenticationResult.INVALID_CREDENTIALS
            assert "Invalid username or password" in result.message

    def test_authenticate_user_totp_required(self):
        """Test authenticate_user when TOTP is required."""
        credentials = DegiroCredentials("testuser", "testpass")
        self.mock_credential_service.validate_credentials.return_value = True

        with (
            patch.object(self.auth_service, "_get_effective_credentials") as mock_get_creds,
            patch.object(self.auth_service, "_authenticate_with_degiro") as mock_auth_degiro,
        ):
            mock_get_creds.return_value = credentials
            mock_auth_degiro.return_value = AuthenticationResponse(
                result=AuthenticationResult.TOTP_REQUIRED, requires_totp=True
            )

            result = self.auth_service.authenticate_user(self.request, "testuser", "testpass")

            assert result.result == AuthenticationResult.TOTP_REQUIRED
            assert result.requires_totp is True
            # Should not store in database when TOTP required
            self.mock_credential_service.store_credentials_in_database.assert_not_called()

    def test_authenticate_user_unexpected_exception(self):
        """Test authenticate_user handles unexpected exceptions."""
        with patch.object(self.auth_service, "_get_effective_credentials", side_effect=Exception("Unexpected error")):
            result = self.auth_service.authenticate_user(self.request)

            assert result.result == AuthenticationResult.UNKNOWN_ERROR
            assert "unexpected error" in result.message.lower()
            # Exception is handled gracefully and error result is returned

    @patch("stonks_overwatch.core.factories.broker_factory.BrokerFactory")
    def test_check_degiro_connection_success(self, mock_factory_class):
        """Test check_degiro_connection successful flow."""
        # Mock broker factory
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_config = Mock()
        mock_config.is_enabled.return_value = True
        mock_config.offline_mode = False
        mock_factory.create_config.return_value = mock_config

        self.mock_degiro_service.check_connection.return_value = True
        self.mock_degiro_service.get_session_id.return_value = "test_session_123"

        result = self.auth_service.check_degiro_connection(self.request)

        assert result.result == AuthenticationResult.SUCCESS
        assert result.session_id == "test_session_123"
        self.mock_session_manager.set_session_id.assert_called_once()
        self.mock_session_manager.set_authenticated.assert_called_once_with(self.request, True)

    @patch("stonks_overwatch.core.factories.broker_factory.BrokerFactory")
    def test_check_degiro_connection_not_enabled(self, mock_factory_class):
        """Test check_degiro_connection when DeGiro is not enabled."""
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_factory.create_config.return_value = None

        result = self.auth_service.check_degiro_connection(self.request)

        assert result.result == AuthenticationResult.CONFIGURATION_ERROR
        assert "not enabled" in result.message

    @patch("stonks_overwatch.core.factories.broker_factory.BrokerFactory")
    def test_check_degiro_connection_offline_mode(self, mock_factory_class):
        """Test check_degiro_connection in offline mode."""
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_config = Mock()
        mock_config.is_enabled.return_value = True
        mock_config.offline_mode = True
        mock_factory.create_config.return_value = mock_config

        result = self.auth_service.check_degiro_connection(self.request)

        assert result.result == AuthenticationResult.SUCCESS
        assert "offline mode" in result.message

    @patch("stonks_overwatch.core.factories.broker_factory.BrokerFactory")
    def test_check_degiro_connection_maintenance_mode(self, mock_factory_class):
        """Test check_degiro_connection during maintenance mode."""
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_config = Mock()
        mock_config.is_enabled.return_value = True
        mock_config.offline_mode = False
        mock_factory.create_config.return_value = mock_config

        # Work around MaintenanceError constructor issue by monkey-patching
        error_details = Mock()
        error_details.error = "System maintenance"

        # Temporarily patch MaintenanceError constructor
        original_init = MaintenanceError.__init__

        def mock_init(self, message, error_details=None):
            Exception.__init__(self, message)
            self.error_details = error_details

        MaintenanceError.__init__ = mock_init
        try:
            error = MaintenanceError("System maintenance", error_details)
        finally:
            # Restore original constructor
            MaintenanceError.__init__ = original_init
        self.mock_degiro_service.check_connection.side_effect = error

        result = self.auth_service.check_degiro_connection(self.request)

        assert result.result == AuthenticationResult.MAINTENANCE_MODE
        assert result.is_maintenance_mode is True

    def test_handle_totp_authentication_success(self):
        """Test handle_totp_authentication successful flow."""
        credentials = DegiroCredentials("testuser", "testpass")
        self.mock_session_manager.get_credentials.return_value = credentials

        with patch.object(self.auth_service, "_authenticate_with_degiro") as mock_auth_degiro:
            mock_auth_degiro.return_value = AuthenticationResponse(
                result=AuthenticationResult.SUCCESS, session_id="test_session_123"
            )

            result = self.auth_service.handle_totp_authentication(self.request, 123456)

            assert result.is_success
            self.mock_session_manager.set_totp_required.assert_called_once_with(self.request, False)
            self.mock_credential_service.merge_credentials.assert_called_once()

    def test_handle_totp_authentication_no_credentials(self):
        """Test handle_totp_authentication when no credentials in session."""
        self.mock_session_manager.get_credentials.return_value = None

        result = self.auth_service.handle_totp_authentication(self.request, 123456)

        assert result.result == AuthenticationResult.CONFIGURATION_ERROR
        assert "No credentials found" in result.message

    def test_handle_totp_authentication_failure(self):
        """Test handle_totp_authentication when TOTP authentication fails."""
        credentials = DegiroCredentials("testuser", "testpass")
        self.mock_session_manager.get_credentials.return_value = credentials

        with patch.object(self.auth_service, "_authenticate_with_degiro") as mock_auth_degiro:
            mock_auth_degiro.return_value = AuthenticationResponse(
                result=AuthenticationResult.INVALID_CREDENTIALS, message="Invalid TOTP code"
            )

            result = self.auth_service.handle_totp_authentication(self.request, 123456)

            assert result.result == AuthenticationResult.INVALID_CREDENTIALS
            # Should not clear TOTP requirement on failure
            self.mock_session_manager.set_totp_required.assert_not_called()

    def test_handle_totp_authentication_exception(self):
        """Test handle_totp_authentication handles exceptions gracefully."""
        self.mock_session_manager.get_credentials.side_effect = Exception("Session error")

        result = self.auth_service.handle_totp_authentication(self.request, 123456)

        assert result.result == AuthenticationResult.UNKNOWN_ERROR
        # Exception is handled gracefully and error result is returned

    def test_logout_user(self):
        """Test logout_user clears session data."""
        self.auth_service.logout_user(self.request)

        self.mock_session_manager.clear_session.assert_called_once_with(self.request)

    def test_logout_user_with_exception(self):
        """Test logout_user handles exceptions gracefully."""
        self.mock_session_manager.clear_session.side_effect = Exception("Logout error")

        # Should not raise exception - error is handled gracefully
        self.auth_service.logout_user(self.request)

    @patch("stonks_overwatch.core.factories.broker_factory.BrokerFactory")
    def test_is_degiro_enabled_true(self, mock_factory_class):
        """Test is_degiro_enabled returns True when DeGiro is enabled."""
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_config = Mock()
        mock_config.is_enabled.return_value = True
        mock_factory.create_config.return_value = mock_config

        result = self.auth_service.is_degiro_enabled()

        assert result is True

    @patch("stonks_overwatch.core.factories.broker_factory.BrokerFactory")
    def test_is_degiro_enabled_false(self, mock_factory_class):
        """Test is_degiro_enabled returns False when DeGiro is disabled."""
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_factory.create_config.return_value = None

        result = self.auth_service.is_degiro_enabled()

        assert result is False

    @patch("stonks_overwatch.core.factories.broker_factory.BrokerFactory")
    def test_is_offline_mode_true(self, mock_factory_class):
        """Test is_offline_mode returns True when offline mode is enabled."""
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_config = Mock()
        mock_config.offline_mode = True
        mock_factory.create_config.return_value = mock_config

        result = self.auth_service.is_offline_mode()

        assert result is True

    @patch("stonks_overwatch.core.factories.broker_factory.BrokerFactory")
    def test_is_offline_mode_false(self, mock_factory_class):
        """Test is_offline_mode returns False when offline mode is disabled."""
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_config = Mock()
        mock_config.offline_mode = False
        mock_factory.create_config.return_value = mock_config

        result = self.auth_service.is_offline_mode()

        assert result is False

    def test_is_maintenance_mode_allowed_true(self):
        """Test is_maintenance_mode_allowed returns True when allowed."""
        self.mock_degiro_service.is_maintenance_mode = True
        self.mock_credential_service.has_default_credentials.return_value = True

        result = self.auth_service.is_maintenance_mode_allowed()

        assert result is True

    def test_is_maintenance_mode_allowed_false_not_maintenance(self):
        """Test is_maintenance_mode_allowed returns False when not in maintenance mode."""
        self.mock_degiro_service.is_maintenance_mode = False

        result = self.auth_service.is_maintenance_mode_allowed()

        assert result is False

    def test_is_maintenance_mode_allowed_false_no_credentials(self):
        """Test is_maintenance_mode_allowed returns False when no default credentials."""
        self.mock_degiro_service.is_maintenance_mode = True
        self.mock_credential_service.has_default_credentials.return_value = False

        result = self.auth_service.is_maintenance_mode_allowed()

        assert result is False

    def test_should_check_connection_with_default_credentials(self):
        """Test should_check_connection returns True when default credentials exist."""
        self.mock_credential_service.has_default_credentials.return_value = True
        self.mock_session_manager.get_session_id.return_value = None

        result = self.auth_service.should_check_connection(self.request)

        assert result is True

    def test_should_check_connection_with_session_id(self):
        """Test should_check_connection returns True when session ID exists."""
        self.mock_credential_service.has_default_credentials.return_value = False
        self.mock_session_manager.get_session_id.return_value = "test_session_123"

        result = self.auth_service.should_check_connection(self.request)

        assert result is True

    def test_should_check_connection_false(self):
        """Test should_check_connection returns False when no credentials or session ID."""
        self.mock_credential_service.has_default_credentials.return_value = False
        self.mock_session_manager.get_session_id.return_value = None

        result = self.auth_service.should_check_connection(self.request)

        assert result is False

    def test_get_authentication_status(self):
        """Test get_authentication_status returns comprehensive status."""
        # Setup mock returns
        self.mock_session_manager.is_authenticated.return_value = True
        self.mock_session_manager.get_session_data.return_value = {"session": "data"}
        self.mock_credential_service.get_credential_sources.return_value = (True, False, True)
        self.mock_degiro_service.is_maintenance_mode = False

        with (
            patch.object(self.auth_service, "is_degiro_enabled") as mock_enabled,
            patch.object(self.auth_service, "is_offline_mode") as mock_offline,
            patch.object(self.auth_service, "is_maintenance_mode_allowed") as mock_maintenance,
            patch.object(self.auth_service, "should_check_connection") as mock_should_check,
        ):
            mock_enabled.return_value = True
            mock_offline.return_value = False
            mock_maintenance.return_value = False
            mock_should_check.return_value = True

            result = self.auth_service.get_authentication_status(self.request)

            assert result["is_authenticated"] is True
            assert result["degiro_enabled"] is True
            assert result["offline_mode"] is False
            assert result["maintenance_mode"] is False
            assert result["maintenance_allowed"] is False
            assert result["should_check_connection"] is True
            assert result["session_data"] == {"session": "data"}
            assert result["credential_sources"] == (True, False, True)

    def test_handle_authentication_error_degiro_connection_error(self):
        """Test handle_authentication_error with DeGiroConnectionError."""
        credentials = DegiroCredentials("testuser", "testpass")
        error_details = Mock()
        error_details.status_text = "invalidCredentials"
        error = DeGiroConnectionError("Invalid credentials", error_details)

        with patch.object(self.auth_service, "_handle_degiro_connection_error") as mock_handle:
            mock_handle.return_value = AuthenticationResponse(
                result=AuthenticationResult.INVALID_CREDENTIALS, message="Invalid credentials"
            )

            result = self.auth_service.handle_authentication_error(self.request, error, credentials)

            assert result.result == AuthenticationResult.INVALID_CREDENTIALS
            mock_handle.assert_called_once_with(self.request, error, credentials)

    def test_handle_authentication_error_maintenance_error(self):
        """Test handle_authentication_error with MaintenanceError."""
        # Work around MaintenanceError constructor issue by monkey-patching
        error_details = Mock()
        error_details.error = "System maintenance"

        # Temporarily patch MaintenanceError constructor
        original_init = MaintenanceError.__init__

        def mock_init(self, message, error_details=None):
            Exception.__init__(self, message)
            self.error_details = error_details

        MaintenanceError.__init__ = mock_init
        try:
            error = MaintenanceError("System maintenance", error_details)
        finally:
            # Restore original constructor
            MaintenanceError.__init__ = original_init

        result = self.auth_service.handle_authentication_error(self.request, error)

        # Since MaintenanceError inherits from DeGiroConnectionError, it's handled as invalid credentials
        assert result.result == AuthenticationResult.INVALID_CREDENTIALS

    def test_handle_authentication_error_connection_error(self):
        """Test handle_authentication_error with ConnectionError."""
        error = ConnectionError("Network error")

        result = self.auth_service.handle_authentication_error(self.request, error)

        assert result.result == AuthenticationResult.CONNECTION_ERROR
        assert "Network connection error" in result.message

    def test_handle_authentication_error_unknown_error(self):
        """Test handle_authentication_error with unknown error."""
        error = ValueError("Unknown error")

        result = self.auth_service.handle_authentication_error(self.request, error)

        assert result.result == AuthenticationResult.UNKNOWN_ERROR
        assert "Unknown error" in result.message

    def test_get_effective_credentials(self):
        """Test _get_effective_credentials merges credentials correctly."""
        base_credentials = DegiroCredentials("baseuser", "basepass")
        self.mock_credential_service.get_effective_credentials.return_value = base_credentials
        merged_credentials = DegiroCredentials("newuser", "basepass", remember_me=True)
        self.mock_credential_service.merge_credentials.return_value = merged_credentials

        result = self.auth_service._get_effective_credentials(self.request, "newuser", None, 123456, True)

        assert result == merged_credentials
        self.mock_credential_service.merge_credentials.assert_called_once_with(
            base_credentials, username="newuser", password=None, one_time_password=123456, remember_me=True
        )

    @patch("stonks_overwatch.services.utilities.authentication_service.Credentials")
    @patch("stonks_overwatch.services.utilities.authentication_service.CredentialsManager")
    def test_authenticate_with_degiro_success(self, mock_creds_manager, mock_credentials):
        """Test _authenticate_with_degiro successful authentication."""
        credentials = DegiroCredentials("testuser", "testpass", one_time_password=123456)
        self.mock_degiro_service.get_session_id.return_value = "test_session_123"

        result = self.auth_service._authenticate_with_degiro(self.request, credentials)

        assert result.result == AuthenticationResult.SUCCESS
        assert result.session_id == "test_session_123"
        mock_credentials.assert_called_once()
        mock_creds_manager.assert_called_once()
        self.mock_degiro_service.set_credentials.assert_called_once()
        self.mock_degiro_service.connect.assert_called_once()
        self.mock_session_manager.set_authenticated.assert_called_once_with(self.request, True)
        self.mock_session_manager.set_session_id.assert_called_once_with(self.request, "test_session_123")

    def test_authenticate_with_degiro_totp_needed(self):
        """Test _authenticate_with_degiro when TOTP is needed."""
        credentials = DegiroCredentials("testuser", "testpass")
        error_details = Mock()
        error_details.status_text = "totpNeeded"
        error = DeGiroConnectionError("TOTP needed", error_details)
        error.error_details = Mock()
        error.error_details.status_text = "totpNeeded"
        self.mock_degiro_service.connect.side_effect = error

        result = self.auth_service._authenticate_with_degiro(self.request, credentials)

        assert result.result == AuthenticationResult.TOTP_REQUIRED
        assert result.requires_totp is True
        self.mock_session_manager.set_totp_required.assert_called_once_with(self.request, True)
        self.mock_session_manager.store_credentials.assert_called_once()

    def test_authenticate_with_degiro_maintenance_error(self):
        """Test _authenticate_with_degiro during maintenance mode."""
        credentials = DegiroCredentials("testuser", "testpass")
        # Work around MaintenanceError constructor issue by monkey-patching
        error_details = Mock()
        error_details.error = "System maintenance"
        error_details.status_text = None  # Ensure status_text is None to avoid TOTP path

        # Temporarily patch MaintenanceError constructor
        original_init = MaintenanceError.__init__

        def mock_init(self, message, error_details=None):
            Exception.__init__(self, message)
            self.error_details = error_details

        MaintenanceError.__init__ = mock_init
        try:
            error = MaintenanceError("System maintenance", error_details)
        finally:
            # Restore original constructor
            MaintenanceError.__init__ = original_init
        self.mock_degiro_service.connect.side_effect = error

        result = self.auth_service._authenticate_with_degiro(self.request, credentials)

        # MaintenanceError should now result in MAINTENANCE_MODE
        assert result.result == AuthenticationResult.MAINTENANCE_MODE
        assert getattr(result, "is_maintenance_mode", True) is True

    def test_dependency_injection_defaults(self):
        """Test AuthenticationService creates default dependencies when none provided."""
        with (
            patch(
                "stonks_overwatch.services.utilities.authentication_service.AuthenticationSessionManager"
            ) as mock_session,
            patch(
                "stonks_overwatch.services.utilities.authentication_service.AuthenticationCredentialService"
            ) as mock_cred,
            patch("stonks_overwatch.services.utilities.authentication_service.DeGiroService") as mock_degiro,
        ):
            service = AuthenticationService()

            # Verify default dependencies were created
            assert service.session_manager is not None
            assert service.credential_service is not None
            assert service.degiro_service is not None
            mock_session.assert_called_once()
            mock_cred.assert_called_once()
            mock_degiro.assert_called_once()

    def test_dependency_injection_with_provided_services(self):
        """Test AuthenticationService uses provided dependencies."""
        mock_session = Mock()
        mock_cred = Mock()
        mock_degiro = Mock()

        service = AuthenticationService(
            session_manager=mock_session, credential_service=mock_cred, degiro_service=mock_degiro
        )

        assert service.session_manager == mock_session
        assert service.credential_service == mock_cred
        assert service.degiro_service == mock_degiro
