"""
Unit tests for Login view (Broker Selector).

This module tests the login view which now serves as a broker selector,
allowing users to choose which broker they want to authenticate with.
"""

from stonks_overwatch.constants import BrokerName
from stonks_overwatch.views.login import Login

import pytest
from django.test import RequestFactory, TestCase
from unittest.mock import Mock, patch


@pytest.mark.django_db
class TestLoginView(TestCase):
    """Test cases for Login view (Broker Selector)."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.view = Login()

    @patch("stonks_overwatch.views.login.BrokerRegistry")
    @patch("stonks_overwatch.views.login.BrokerFactory")
    def test_get_shows_broker_selector(self, mock_factory_class, mock_registry_class):
        """Test GET request shows broker selector with available brokers."""
        # Mock the registry and factory instances
        mock_registry = Mock()
        mock_factory = Mock()
        mock_registry_class.return_value = mock_registry
        mock_factory_class.return_value = mock_factory

        # Mock registered brokers
        mock_registry.get_registered_brokers.return_value = [BrokerName.DEGIRO, BrokerName.BITVAVO, BrokerName.IBKR]

        # Mock broker configurations - enabled but NO stored credentials
        mock_degiro_config = Mock()
        mock_degiro_config.is_enabled.return_value = True
        mock_degiro_config.get_credentials = None  # No stored credentials
        mock_bitvavo_config = Mock()
        mock_bitvavo_config.is_enabled.return_value = False
        mock_bitvavo_config.get_credentials = None
        mock_ibkr_config = Mock()
        mock_ibkr_config.is_enabled.return_value = False
        mock_ibkr_config.get_credentials = None

        mock_factory.create_config.side_effect = lambda broker: {
            BrokerName.DEGIRO: mock_degiro_config,
            BrokerName.BITVAVO: mock_bitvavo_config,
            BrokerName.IBKR: mock_ibkr_config,
        }.get(broker)

        # Create view AFTER mocks are set up so it uses mocked factory/registry
        view = Login()
        request = self.factory.get("/login/")
        response = view.get(request)

        assert response.status_code == 200
        content = response.content.decode("utf-8")

        # Check that broker selector is shown
        assert "Select Your Broker" in content or "broker" in content.lower()
        assert "DEGIRO" in content
        assert "Bitvavo" in content
        assert "Interactive Brokers" in content

    @patch("stonks_overwatch.views.login.BrokerRegistry")
    @patch("stonks_overwatch.views.login.BrokerFactory")
    def test_get_handles_broker_config_error(self, mock_factory_class, mock_registry_class):
        """Test GET request handles broker configuration errors gracefully."""
        # Mock the registry and factory instances
        mock_registry = Mock()
        mock_factory = Mock()
        mock_registry_class.return_value = mock_registry
        mock_factory_class.return_value = mock_factory

        # Mock registered brokers
        mock_registry.get_registered_brokers.return_value = [BrokerName.DEGIRO, BrokerName.BITVAVO]

        # Mock factory to raise exception for one broker
        def mock_create_config(broker):
            if broker == BrokerName.DEGIRO:
                mock_config = Mock()
                mock_config.is_enabled.return_value = True
                mock_config.get_credentials = None  # No stored credentials
                return mock_config
            elif broker == BrokerName.BITVAVO:
                raise Exception("Configuration error")
            return None

        mock_factory.create_config.side_effect = mock_create_config

        # Create view AFTER mocks are set up so it uses mocked factory/registry
        view = Login()
        request = self.factory.get("/login/")
        response = view.get(request)

        assert response.status_code == 200
        content = response.content.decode("utf-8")

        # Should still show broker selector with available brokers
        assert "DEGIRO" in content
        assert "Bitvavo" in content  # Should still be shown even with config error

    def test_post_redirects_to_login(self):
        """Test POST request redirects back to login (broker selector)."""
        request = self.factory.post("/login/", {})
        response = self.view.post(request)

        assert response.status_code == 302
        assert response["Location"] == "/login"

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

    def test_get_broker_description(self):
        """Test _get_broker_description returns appropriate descriptions."""
        assert "European" in self.view._get_broker_description(BrokerName.DEGIRO)
        assert "cryptocurrency" in self.view._get_broker_description(BrokerName.BITVAVO)
        assert "Global" in self.view._get_broker_description(BrokerName.IBKR)
        assert self.view._get_broker_description("unknown") == "Investment platform"

    @patch("stonks_overwatch.views.login.BrokerRegistry")
    @patch("stonks_overwatch.views.login.PortfolioId")
    @patch("stonks_overwatch.views.login.BrokerFactory")
    def test_get_available_brokers_sorting(self, mock_factory_class, mock_portfolio_id, mock_registry_class):
        """Test that available brokers are sorted alphabetically by display name."""
        # Mock the registry and factory instances
        mock_registry = Mock()
        mock_factory = Mock()
        mock_registry_class.return_value = mock_registry
        mock_factory_class.return_value = mock_factory

        # Mock registered brokers
        mock_registry.get_registered_brokers.return_value = [BrokerName.IBKR, BrokerName.DEGIRO, BrokerName.BITVAVO]

        # Mock broker configurations
        mock_degiro_config = Mock()
        mock_degiro_config.is_enabled.return_value = True
        mock_bitvavo_config = Mock()
        mock_bitvavo_config.is_enabled.return_value = False
        mock_ibkr_config = Mock()
        mock_ibkr_config.is_enabled.return_value = True

        mock_factory.create_config.side_effect = lambda broker: {
            BrokerName.DEGIRO: mock_degiro_config,
            BrokerName.BITVAVO: mock_bitvavo_config,
            BrokerName.IBKR: mock_ibkr_config,
        }.get(broker)

        # Mock PortfolioId.from_broker_name to return mock portfolio objects with stable attribute
        def mock_from_broker_name(broker):
            mock_portfolio = Mock()
            mock_portfolio.stable = True if broker == BrokerName.DEGIRO else False
            return mock_portfolio

        mock_portfolio_id.from_broker_name.side_effect = mock_from_broker_name

        # Create view AFTER mocks are set up so it uses mocked factory/registry
        view = Login()
        brokers = view._get_available_brokers()

        # Should have 3 brokers
        assert len(brokers) == 3

        # Brokers should be sorted alphabetically by display name
        display_names = [b["display_name"] for b in brokers]
        assert display_names == sorted(display_names)

        # Verify order: Bitvavo, DEGIRO, IBKR (alphabetical)
        assert brokers[0]["name"] == "bitvavo"
        assert brokers[1]["name"] == "degiro"
        assert brokers[2]["name"] == "ibkr"

    @patch("stonks_overwatch.views.login.BrokerRegistry")
    @patch("stonks_overwatch.views.login.BrokerFactory")
    def test_render_broker_selector_exception_handling(self, mock_factory_class, mock_registry_class):
        """Test that _render_broker_selector handles exceptions gracefully."""
        # Mock the registry to raise an exception
        mock_registry = Mock()
        mock_factory = Mock()
        mock_registry_class.return_value = mock_registry
        mock_factory_class.return_value = mock_factory

        mock_registry.get_registered_brokers.side_effect = Exception("Registry error")

        request = self.factory.get("/login/")
        response = self.view._render_broker_selector(request)

        # Should return 200 status with empty broker list (graceful degradation)
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        # Should contain basic HTML structure even with error
        assert "<html>" in content or "<!DOCTYPE" in content
