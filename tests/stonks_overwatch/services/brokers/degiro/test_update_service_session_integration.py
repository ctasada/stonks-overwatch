"""
Tests for UpdateService session integration.

These tests verify that UpdateService properly checks for active sessions
before proceeding with updates.
"""

from stonks_overwatch.services.brokers.degiro.services.update_service import UpdateService

import pytest
from unittest.mock import Mock, patch


class TestUpdateServiceSessionIntegration:
    """Test UpdateService integration with session checking."""

    @pytest.fixture
    def mock_config(self):
        """Mock DeGiro configuration."""
        config = Mock()
        config.get_credentials.has_minimal_credentials.return_value = True
        return config

    @pytest.fixture
    def mock_degiro_service(self):
        """Mock DeGiroService."""
        service = Mock()
        service.check_connection.return_value = True
        return service

    def test_update_all_with_active_session_proceeds(self, mock_config, mock_degiro_service):
        """Test that update_all proceeds when active session exists."""
        with (
            patch(
                "stonks_overwatch.services.brokers.degiro.services.session_checker.DeGiroSessionChecker.has_active_session"
            ) as mock_has_session,
            patch(
                "stonks_overwatch.services.brokers.degiro.services.update_service.DeGiroService"
            ) as mock_degiro_class,
            patch("stonks_overwatch.core.factories.broker_factory.BrokerFactory") as mock_factory_class,
        ):
            # Mock active session exists
            mock_has_session.return_value = True

            # Mock factory and service creation
            mock_factory = Mock()
            mock_factory_class.return_value = mock_factory
            mock_factory.create_config.return_value = mock_config

            mock_degiro_class.return_value = mock_degiro_service

            # Create UpdateService
            update_service = UpdateService(config=mock_config)

            # Mock the individual update methods to avoid database dependencies
            with (
                patch.object(update_service, "update_account") as mock_update_account,
                patch.object(update_service, "update_transactions") as mock_update_transactions,
                patch.object(update_service, "update_portfolio") as mock_update_portfolio,
                patch.object(update_service, "update_company_profile") as mock_update_company_profile,
                patch.object(update_service, "update_yfinance") as mock_update_yfinance,
                patch.object(update_service, "update_dividends") as mock_update_dividends,
            ):
                # Call update_all
                update_service.update_all()

                # Verify session check was called
                mock_has_session.assert_called_once()

                # Verify connection check was called
                mock_degiro_service.check_connection.assert_called_once()

                # Verify all update methods were called (since session exists)
                mock_update_account.assert_called_once()
                mock_update_transactions.assert_called_once()
                mock_update_portfolio.assert_called_once()
                mock_update_company_profile.assert_called_once()
                mock_update_yfinance.assert_called_once()
                mock_update_dividends.assert_called_once()

    def test_update_all_no_active_session_skips_update(self, mock_config, mock_degiro_service):
        """Test that update_all skips update when no active session."""
        with (
            patch(
                "stonks_overwatch.services.brokers.degiro.services.session_checker.DeGiroSessionChecker.has_active_session"
            ) as mock_has_session,
            patch(
                "stonks_overwatch.services.brokers.degiro.services.update_service.DeGiroService"
            ) as mock_degiro_class,
            patch("stonks_overwatch.core.factories.broker_factory.BrokerFactory") as mock_factory_class,
        ):
            # Mock no active session
            mock_has_session.return_value = False

            # Mock factory and service creation
            mock_factory = Mock()
            mock_factory_class.return_value = mock_factory
            mock_factory.create_config.return_value = mock_config

            mock_degiro_class.return_value = mock_degiro_service

            # Create UpdateService
            update_service = UpdateService(config=mock_config)

            # Mock the individual update methods
            with (
                patch.object(update_service, "update_account") as mock_update_account,
                patch.object(update_service, "update_transactions") as mock_update_transactions,
                patch.object(update_service, "update_portfolio") as mock_update_portfolio,
                patch.object(update_service, "update_company_profile") as mock_update_company_profile,
                patch.object(update_service, "update_yfinance") as mock_update_yfinance,
                patch.object(update_service, "update_dividends") as mock_update_dividends,
            ):
                # Call update_all
                update_service.update_all()

                # Verify session check was called
                mock_has_session.assert_called_once()

                # Verify connection check was NOT called (early return due to no session)
                mock_degiro_service.check_connection.assert_not_called()

                # Verify NO update methods were called (due to no session)
                mock_update_account.assert_not_called()
                mock_update_transactions.assert_not_called()
                mock_update_portfolio.assert_not_called()
                mock_update_company_profile.assert_not_called()
                mock_update_yfinance.assert_not_called()
                mock_update_dividends.assert_not_called()

    def test_update_all_session_exists_but_connection_fails(self, mock_config, mock_degiro_service):
        """Test update_all when session exists but connection check fails."""
        with (
            patch(
                "stonks_overwatch.services.brokers.degiro.services.session_checker.DeGiroSessionChecker.has_active_session"
            ) as mock_has_session,
            patch(
                "stonks_overwatch.services.brokers.degiro.services.update_service.DeGiroService"
            ) as mock_degiro_class,
            patch("stonks_overwatch.core.factories.broker_factory.BrokerFactory") as mock_factory_class,
        ):
            # Mock active session exists
            mock_has_session.return_value = True

            # Mock connection failure
            mock_degiro_service.check_connection.return_value = False

            # Mock factory and service creation
            mock_factory = Mock()
            mock_factory_class.return_value = mock_factory
            mock_factory.create_config.return_value = mock_config

            mock_degiro_class.return_value = mock_degiro_service

            # Create UpdateService
            update_service = UpdateService(config=mock_config)

            # Mock the individual update methods
            with patch.object(update_service, "update_account") as mock_update_account:
                # Call update_all
                update_service.update_all()

                # Verify session check was called and passed
                mock_has_session.assert_called_once()

                # Verify connection check was called and failed
                mock_degiro_service.check_connection.assert_called_once()

                # Verify NO update methods were called (due to connection failure)
                mock_update_account.assert_not_called()

    def test_session_checking_order(self, mock_config, mock_degiro_service):
        """Test that session checking happens before connection checking."""
        with (
            patch(
                "stonks_overwatch.services.brokers.degiro.services.session_checker.DeGiroSessionChecker.has_active_session"
            ) as mock_has_session,
            patch(
                "stonks_overwatch.services.brokers.degiro.services.update_service.DeGiroService"
            ) as mock_degiro_class,
            patch("stonks_overwatch.core.factories.broker_factory.BrokerFactory") as mock_factory_class,
        ):
            # Mock no active session
            mock_has_session.return_value = False

            # Mock factory and service creation
            mock_factory = Mock()
            mock_factory_class.return_value = mock_factory
            mock_factory.create_config.return_value = mock_config

            mock_degiro_class.return_value = mock_degiro_service

            # Create UpdateService
            update_service = UpdateService(config=mock_config)

            # Call update_all
            update_service.update_all()

            # Verify session check was called
            mock_has_session.assert_called_once()

            # Verify connection check was NOT called (should not reach this due to no session)
            mock_degiro_service.check_connection.assert_not_called()

            # This confirms that session checking happens first and prevents unnecessary connection checks
