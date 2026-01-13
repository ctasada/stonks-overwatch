"""
Unit tests for Login view (Broker Selector).

This module tests the login view which now serves as a broker selector,
allowing users to choose which broker they want to authenticate with.
"""

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
        mock_registry.get_registered_brokers.return_value = ["degiro", "bitvavo", "ibkr"]

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
            "degiro": mock_degiro_config,
            "bitvavo": mock_bitvavo_config,
            "ibkr": mock_ibkr_config,
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
        mock_registry.get_registered_brokers.return_value = ["degiro", "bitvavo"]

        # Mock factory to raise exception for one broker
        def mock_create_config(broker):
            if broker == "degiro":
                mock_config = Mock()
                mock_config.is_enabled.return_value = True
                mock_config.get_credentials = None  # No stored credentials
                return mock_config
            elif broker == "bitvavo":
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

    def test_get_display_name(self):
        """Test _get_display_name returns correct display names."""
        assert self.view._get_display_name("degiro") == "DEGIRO"
        assert self.view._get_display_name("bitvavo") == "Bitvavo"
        assert self.view._get_display_name("ibkr") == "Interactive Brokers"
        assert self.view._get_display_name("unknown") == "Unknown"

    def test_get_broker_description(self):
        """Test _get_broker_description returns appropriate descriptions."""
        assert "European" in self.view._get_broker_description("degiro")
        assert "cryptocurrency" in self.view._get_broker_description("bitvavo")
        assert "Global" in self.view._get_broker_description("ibkr")
        assert self.view._get_broker_description("unknown") == "Investment platform"

    @patch("stonks_overwatch.views.login.BrokerRegistry")
    @patch("stonks_overwatch.views.login.BrokerFactory")
    def test_get_available_brokers_sorting(self, mock_factory_class, mock_registry_class):
        """Test that available brokers are sorted correctly (enabled first, then alphabetically)."""
        # Mock the registry and factory instances
        mock_registry = Mock()
        mock_factory = Mock()
        mock_registry_class.return_value = mock_registry
        mock_factory_class.return_value = mock_factory

        # Mock registered brokers
        mock_registry.get_registered_brokers.return_value = ["ibkr", "degiro", "bitvavo"]

        # Mock broker configurations - make bitvavo enabled, others disabled
        mock_degiro_config = Mock()
        mock_degiro_config.is_enabled.return_value = False
        mock_bitvavo_config = Mock()
        mock_bitvavo_config.is_enabled.return_value = True
        mock_ibkr_config = Mock()
        mock_ibkr_config.is_enabled.return_value = False

        mock_factory.create_config.side_effect = lambda broker: {
            "degiro": mock_degiro_config,
            "bitvavo": mock_bitvavo_config,
            "ibkr": mock_ibkr_config,
        }.get(broker)

        # Create view AFTER mocks are set up so it uses mocked factory/registry
        view = Login()
        brokers = view._get_available_brokers()

        # Should have 3 brokers
        assert len(brokers) == 3

        # First broker should be the enabled one (Bitvavo)
        assert brokers[0]["name"] == "bitvavo"
        assert brokers[0]["enabled"] is True

        # Remaining brokers should be sorted alphabetically by display name
        disabled_brokers = [b for b in brokers if not b["enabled"]]
        display_names = [b["display_name"] for b in disabled_brokers]
        assert display_names == sorted(display_names)

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
