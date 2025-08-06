"""
Unit tests for AuthenticationCredentialService.

This module contains comprehensive tests for the authentication credential service,
including credential validation, storage, retrieval, and merging operations.
"""

from django.http import HttpRequest

from stonks_overwatch.config.degiro import DegiroCredentials
from stonks_overwatch.services.utilities.authentication_credential_service import AuthenticationCredentialService

import pytest
from django.test import TestCase
from unittest.mock import Mock, patch


@pytest.mark.django_db
class TestAuthenticationCredentialService(TestCase):
    """Test cases for AuthenticationCredentialService."""

    def setUp(self):
        """Set up test fixtures."""
        self.credential_service = AuthenticationCredentialService()
        self.request = self._create_mock_request()

    def _create_mock_request(self):
        """Create a mock request with session."""
        request = Mock(spec=HttpRequest)
        request.session = {}
        return request

    def test_validate_credentials_valid(self):
        """Test validate_credentials returns True for valid credentials."""
        result = self.credential_service.validate_credentials("testuser", "password123")

        assert result is True

    def test_validate_credentials_empty_username(self):
        """Test validate_credentials returns False for empty username."""
        result = self.credential_service.validate_credentials("", "password123")

        assert result is False

    def test_validate_credentials_none_username(self):
        """Test validate_credentials returns False for None username."""
        result = self.credential_service.validate_credentials(None, "password123")

        assert result is False

    def test_validate_credentials_empty_password(self):
        """Test validate_credentials returns False for empty password."""
        result = self.credential_service.validate_credentials("testuser", "")

        assert result is False

    def test_validate_credentials_none_password(self):
        """Test validate_credentials returns False for None password."""
        result = self.credential_service.validate_credentials("testuser", None)

        assert result is False

    def test_validate_credentials_whitespace_username(self):
        """Test validate_credentials returns False for whitespace-only username."""
        result = self.credential_service.validate_credentials("   ", "password123")

        assert result is False

    def test_validate_credentials_whitespace_password(self):
        """Test validate_credentials returns False for whitespace-only password."""
        result = self.credential_service.validate_credentials("testuser", "   ")

        assert result is False

    def test_validate_credentials_short_username(self):
        """Test validate_credentials returns False for too short username."""
        result = self.credential_service.validate_credentials("a", "password123")

        assert result is False

    def test_validate_credentials_short_password(self):
        """Test validate_credentials returns False for too short password."""
        result = self.credential_service.validate_credentials("testuser", "123")

        assert result is False

    def test_validate_credentials_with_exception(self):
        """Test validate_credentials handles exceptions gracefully."""
        with patch.object(self.credential_service, "logger") as mock_logger:
            # Force an exception by passing a non-string object that will cause an error
            # when the method tries to call .strip() on it
            invalid_input = Mock()
            invalid_input.strip.side_effect = Exception("Test error")

            result = self.credential_service.validate_credentials(invalid_input, "password123")

            assert result is False
            mock_logger.error.assert_called()

    def test_get_credentials_from_session_exists(self):
        """Test get_credentials_from_session returns credentials when they exist."""
        credentials_data = {"username": "testuser", "password": "testpass", "remember_me": True}
        self.request.session["credentials"] = credentials_data

        result = self.credential_service.get_credentials_from_session(self.request)

        assert isinstance(result, DegiroCredentials)
        assert result.username == "testuser"
        assert result.password == "testpass"
        assert result.remember_me is True

    def test_get_credentials_from_session_not_exists(self):
        """Test get_credentials_from_session returns None when credentials don't exist."""
        result = self.credential_service.get_credentials_from_session(self.request)

        assert result is None

    def test_get_credentials_from_session_incomplete(self):
        """Test get_credentials_from_session returns None for incomplete credentials."""
        credentials_data = {"username": "testuser"}  # Missing password
        self.request.session["credentials"] = credentials_data

        result = self.credential_service.get_credentials_from_session(self.request)

        assert result is None

    @patch("stonks_overwatch.services.brokers.models.BrokersConfigurationRepository")
    def test_get_credentials_from_database_exists(self, mock_repository):
        """Test get_credentials_from_database returns credentials when they exist."""
        # Mock broker configuration with credentials
        mock_config = Mock()
        mock_config.credentials = {"username": "dbuser", "password": "dbpass"}
        mock_repository.get_broker_by_name.return_value = mock_config

        result = self.credential_service.get_credentials_from_database()

        assert isinstance(result, DegiroCredentials)
        assert result.username == "dbuser"
        assert result.password == "dbpass"
        assert result.remember_me is True

    @patch("stonks_overwatch.services.brokers.models.BrokersConfigurationRepository")
    def test_get_credentials_from_database_not_exists(self, mock_repository):
        """Test get_credentials_from_database returns None when credentials don't exist."""
        mock_config = Mock()
        mock_config.credentials = None
        mock_repository.get_broker_by_name.return_value = mock_config

        result = self.credential_service.get_credentials_from_database()

        assert result is None

    @patch("stonks_overwatch.services.brokers.models.BrokersConfigurationRepository")
    def test_get_credentials_from_database_incomplete(self, mock_repository):
        """Test get_credentials_from_database returns None for incomplete credentials."""
        mock_config = Mock()
        mock_config.credentials = {"username": "dbuser"}  # Missing password
        mock_repository.get_broker_by_name.return_value = mock_config

        result = self.credential_service.get_credentials_from_database()

        assert result is None

    @patch("stonks_overwatch.core.factories.broker_factory.BrokerFactory")
    def test_get_credentials_from_config_exists(self, mock_factory_class):
        """Test get_credentials_from_config returns credentials when they exist."""
        # Mock broker factory and config
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory

        mock_config = Mock()
        mock_credentials = Mock()
        mock_credentials.username = "configuser"
        mock_credentials.password = "configpass"
        mock_credentials.int_account = 12345
        mock_credentials.totp_secret_key = "secret"
        mock_config.credentials = mock_credentials
        mock_config.get_credentials = mock_credentials
        mock_factory.create_config.return_value = mock_config

        result = self.credential_service.get_credentials_from_config()

        assert isinstance(result, DegiroCredentials)
        assert result.username == "configuser"
        assert result.password == "configpass"
        assert result.int_account == 12345
        assert result.totp_secret_key == "secret"
        assert result.remember_me is False

    @patch("stonks_overwatch.core.factories.broker_factory.BrokerFactory")
    def test_get_credentials_from_config_not_exists(self, mock_factory_class):
        """Test get_credentials_from_config returns None when credentials don't exist."""
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_factory.create_config.return_value = None

        result = self.credential_service.get_credentials_from_config()

        assert result is None

    def test_get_effective_credentials_from_session(self):
        """Test get_effective_credentials prioritizes session credentials."""
        # Setup session credentials
        session_credentials = {"username": "sessionuser", "password": "sessionpass"}
        self.request.session["credentials"] = session_credentials

        with (
            patch.object(self.credential_service, "get_credentials_from_database") as mock_db,
            patch.object(self.credential_service, "get_credentials_from_config") as mock_config,
        ):
            mock_db.return_value = DegiroCredentials("dbuser", "dbpass")
            mock_config.return_value = DegiroCredentials("configuser", "configpass")

            result = self.credential_service.get_effective_credentials(self.request)

            assert result.username == "sessionuser"
            assert result.password == "sessionpass"

    def test_get_effective_credentials_from_database(self):
        """Test get_effective_credentials falls back to database credentials."""
        with (
            patch.object(self.credential_service, "get_credentials_from_session") as mock_session,
            patch.object(self.credential_service, "get_credentials_from_database") as mock_db,
            patch.object(self.credential_service, "get_credentials_from_config") as mock_config,
        ):
            mock_session.return_value = None
            mock_db.return_value = DegiroCredentials("dbuser", "dbpass")
            mock_config.return_value = DegiroCredentials("configuser", "configpass")

            result = self.credential_service.get_effective_credentials(self.request)

            assert result.username == "dbuser"
            assert result.password == "dbpass"

    def test_get_effective_credentials_from_config(self):
        """Test get_effective_credentials falls back to config credentials."""
        with (
            patch.object(self.credential_service, "get_credentials_from_session") as mock_session,
            patch.object(self.credential_service, "get_credentials_from_database") as mock_db,
            patch.object(self.credential_service, "get_credentials_from_config") as mock_config,
        ):
            mock_session.return_value = None
            mock_db.return_value = None
            mock_config.return_value = DegiroCredentials("configuser", "configpass")

            result = self.credential_service.get_effective_credentials(self.request)

            assert result.username == "configuser"
            assert result.password == "configpass"

    def test_get_effective_credentials_none_available(self):
        """Test get_effective_credentials returns None when no credentials available."""
        with (
            patch.object(self.credential_service, "get_credentials_from_session") as mock_session,
            patch.object(self.credential_service, "get_credentials_from_database") as mock_db,
            patch.object(self.credential_service, "get_credentials_from_config") as mock_config,
        ):
            mock_session.return_value = None
            mock_db.return_value = None
            mock_config.return_value = None

            result = self.credential_service.get_effective_credentials(self.request)

            assert result is None

    @patch("stonks_overwatch.services.brokers.models.BrokersConfigurationRepository")
    def test_store_credentials_in_database_success(self, mock_repository):
        """Test store_credentials_in_database stores credentials successfully."""
        mock_config = Mock()
        mock_config.credentials = {}
        mock_repository.get_broker_by_name.return_value = mock_config

        result = self.credential_service.store_credentials_in_database("testuser", "testpass")

        assert result is True
        assert mock_config.credentials["username"] == "testuser"
        assert mock_config.credentials["password"] == "testpass"
        mock_repository.save_broker_configuration.assert_called_once_with(mock_config)

    @patch("stonks_overwatch.services.brokers.models.BrokersConfigurationRepository")
    def test_store_credentials_in_database_new_credentials_dict(self, mock_repository):
        """Test store_credentials_in_database creates new credentials dict if None."""
        mock_config = Mock()
        mock_config.credentials = None
        mock_repository.get_broker_by_name.return_value = mock_config

        result = self.credential_service.store_credentials_in_database("testuser", "testpass")

        assert result is True
        assert mock_config.credentials["username"] == "testuser"
        assert mock_config.credentials["password"] == "testpass"

    @patch("stonks_overwatch.services.brokers.models.BrokersConfigurationRepository")
    def test_store_credentials_in_database_failure(self, mock_repository):
        """Test store_credentials_in_database handles exceptions gracefully."""
        mock_repository.get_broker_by_name.side_effect = Exception("Database error")

        result = self.credential_service.store_credentials_in_database("testuser", "testpass")

        assert result is False

    def test_has_stored_credentials_from_database(self):
        """Test has_stored_credentials returns True when database has credentials."""
        with (
            patch.object(self.credential_service, "get_credentials_from_database") as mock_db,
            patch.object(self.credential_service, "get_credentials_from_config") as mock_config,
        ):
            mock_db.return_value = DegiroCredentials("dbuser", "dbpass")
            mock_config.return_value = None

            result = self.credential_service.has_stored_credentials()

            assert result is True

    def test_has_stored_credentials_from_config(self):
        """Test has_stored_credentials returns True when config has credentials."""
        with (
            patch.object(self.credential_service, "get_credentials_from_database") as mock_db,
            patch.object(self.credential_service, "get_credentials_from_config") as mock_config,
        ):
            mock_db.return_value = None
            mock_config.return_value = DegiroCredentials("configuser", "configpass")

            result = self.credential_service.has_stored_credentials()

            assert result is True

    def test_has_stored_credentials_none(self):
        """Test has_stored_credentials returns False when no credentials exist."""
        with (
            patch.object(self.credential_service, "get_credentials_from_database") as mock_db,
            patch.object(self.credential_service, "get_credentials_from_config") as mock_config,
        ):
            mock_db.return_value = None
            mock_config.return_value = None

            result = self.credential_service.has_stored_credentials()

            assert result is False

    def test_has_default_credentials_true(self):
        """Test has_default_credentials returns True when config credentials exist."""
        with patch.object(self.credential_service, "get_credentials_from_config") as mock_config:
            mock_config.return_value = DegiroCredentials("configuser", "configpass")

            result = self.credential_service.has_default_credentials()

            assert result is True

    def test_has_default_credentials_false(self):
        """Test has_default_credentials returns False when no config credentials exist."""
        with patch.object(self.credential_service, "get_credentials_from_config") as mock_config:
            mock_config.return_value = None

            result = self.credential_service.has_default_credentials()

            assert result is False

    def test_create_credentials_full(self):
        """Test create_credentials creates credentials with all parameters."""
        result = self.credential_service.create_credentials("testuser", "testpass", 123456, True)

        assert isinstance(result, DegiroCredentials)
        assert result.username == "testuser"
        assert result.password == "testpass"
        assert result.one_time_password == 123456
        assert result.remember_me is True

    def test_create_credentials_minimal(self):
        """Test create_credentials creates credentials with minimal parameters."""
        result = self.credential_service.create_credentials("testuser", "testpass")

        assert isinstance(result, DegiroCredentials)
        assert result.username == "testuser"
        assert result.password == "testpass"
        assert result.one_time_password is None
        assert result.remember_me is False

    def test_merge_credentials_with_base(self):
        """Test merge_credentials merges with existing base credentials."""
        base_credentials = DegiroCredentials(
            username="baseuser", password="basepass", int_account=12345, remember_me=True
        )

        result = self.credential_service.merge_credentials(
            base_credentials, username="newuser", one_time_password=654321
        )

        assert result.username == "newuser"  # Overridden
        assert result.password == "basepass"  # From base
        assert result.int_account == 12345  # From base
        assert result.one_time_password == 654321  # Overridden
        assert result.remember_me is True  # From base

    def test_merge_credentials_without_base(self):
        """Test merge_credentials creates new credentials when no base provided."""
        result = self.credential_service.merge_credentials(
            None, username="newuser", password="newpass", remember_me=True
        )

        assert result.username == "newuser"
        assert result.password == "newpass"
        assert result.int_account is None
        assert result.totp_secret_key is None
        assert result.remember_me is True

    def test_merge_credentials_with_exception(self):
        """Test merge_credentials handles exceptions gracefully."""
        with patch("stonks_overwatch.config.degiro.DegiroCredentials", side_effect=Exception("Merge error")):
            result = self.credential_service.merge_credentials(None, "user", "pass")

            # Should return fallback credentials
            assert isinstance(result, DegiroCredentials)
            assert result.username == "user"
            assert result.password == "pass"

    @patch("stonks_overwatch.services.brokers.models.BrokersConfigurationRepository")
    def test_clear_stored_credentials_success(self, mock_repository):
        """Test clear_stored_credentials clears credentials successfully."""
        mock_config = Mock()
        mock_config.credentials = {"username": "test", "password": "test"}
        mock_repository.get_broker_by_name.return_value = mock_config

        result = self.credential_service.clear_stored_credentials()

        assert result is True
        assert mock_config.credentials == {}
        mock_repository.save_broker_configuration.assert_called_once_with(mock_config)

    @patch("stonks_overwatch.services.brokers.models.BrokersConfigurationRepository")
    def test_clear_stored_credentials_failure(self, mock_repository):
        """Test clear_stored_credentials handles exceptions gracefully."""
        mock_repository.get_broker_by_name.side_effect = Exception("Database error")

        result = self.credential_service.clear_stored_credentials()

        assert result is False

    def test_get_credential_sources_all_true(self):
        """Test get_credential_sources when all sources have credentials."""
        with (
            patch.object(self.credential_service, "_has_session_credentials") as mock_session,
            patch.object(self.credential_service, "_has_database_credentials") as mock_db,
            patch.object(self.credential_service, "_has_config_credentials") as mock_config,
        ):
            mock_session.return_value = True
            mock_db.return_value = True
            mock_config.return_value = True

            result = self.credential_service.get_credential_sources(self.request)

            assert result == (True, True, True)

    def test_get_credential_sources_mixed(self):
        """Test get_credential_sources with mixed source availability."""
        with (
            patch.object(self.credential_service, "_has_session_credentials") as mock_session,
            patch.object(self.credential_service, "_has_database_credentials") as mock_db,
            patch.object(self.credential_service, "_has_config_credentials") as mock_config,
        ):
            mock_session.return_value = True
            mock_db.return_value = False
            mock_config.return_value = True

            result = self.credential_service.get_credential_sources(self.request)

            assert result == (True, False, True)

    def test_get_credential_sources_all_false(self):
        """Test get_credential_sources when no sources have credentials."""
        with (
            patch.object(self.credential_service, "_has_session_credentials") as mock_session,
            patch.object(self.credential_service, "_has_database_credentials") as mock_db,
            patch.object(self.credential_service, "_has_config_credentials") as mock_config,
        ):
            mock_session.return_value = False
            mock_db.return_value = False
            mock_config.return_value = False

            result = self.credential_service.get_credential_sources(self.request)

            assert result == (False, False, False)

    def test_get_credential_sources_with_exception(self):
        """Test get_credential_sources handles exceptions gracefully."""
        with patch.object(self.credential_service, "logger") as mock_logger:
            with patch.object(self.credential_service, "_has_session_credentials", side_effect=Exception("Test error")):
                result = self.credential_service.get_credential_sources(self.request)

                assert result == (False, False, False)
                mock_logger.error.assert_called()

    def test_dependency_injection_with_config(self):
        """Test AuthenticationCredentialService works with dependency injection."""
        mock_config = Mock()
        credential_service = AuthenticationCredentialService(config=mock_config)

        assert credential_service.config == mock_config
        assert credential_service.is_dependency_injection_enabled() is True

    def test_dependency_injection_without_config(self):
        """Test AuthenticationCredentialService works without dependency injection."""
        credential_service = AuthenticationCredentialService()

        assert credential_service.config is not None  # Should use global config
        assert credential_service.is_dependency_injection_enabled() is False
