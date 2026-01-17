"""
Unit tests for RootRedirectView.

This module tests the root redirect view that handles initial routing
based on broker configuration and demo mode.
"""

from django.http import HttpRequest, HttpResponse

from stonks_overwatch.views.root_redirect import RootRedirectView

from django.test import TestCase
from unittest.mock import Mock, patch


class TestRootRedirectView(TestCase):
    """Test cases for RootRedirectView."""

    @patch("stonks_overwatch.views.root_redirect.BrokerRegistry")
    @patch("stonks_overwatch.views.root_redirect.BrokerFactory")
    def setUp(self, mock_factory_class, mock_registry_class):
        """Set up test fixtures."""
        self.mock_factory = Mock()
        self.mock_registry = Mock()

        mock_factory_class.return_value = self.mock_factory
        mock_registry_class.return_value = self.mock_registry

        self.view = RootRedirectView()
        self.request = self._create_mock_request()

    def _create_mock_request(self):
        """Create a mock request with session."""
        request = Mock(spec=HttpRequest)
        request.session = {}
        request.path_info = "/"
        return request

    @patch("stonks_overwatch.views.root_redirect.redirect")
    def test_redirects_to_dashboard_when_authenticated_with_configured_brokers(self, mock_redirect):
        """Test view redirects to dashboard when user is authenticated and brokers are configured."""
        mock_redirect.return_value = HttpResponse(status=302)

        # Mock demo mode detection to return False
        with patch("stonks_overwatch.utils.core.demo_mode.is_demo_mode", return_value=False):
            # Mock configured brokers
            with patch.object(self.view, "_has_configured_brokers", return_value=True):
                # Mock authenticated user
                with patch.object(self.view, "_is_user_authenticated", return_value=True):
                    _response = self.view.get(self.request)

        mock_redirect.assert_called_once_with("dashboard")

    @patch("stonks_overwatch.utils.core.demo_mode.os.getenv")
    def test_is_demo_mode_detects_environment_variable(self, mock_getenv):
        """Test is_demo_mode correctly detects DEMO_MODE environment variable."""
        from stonks_overwatch.utils.core.demo_mode import is_demo_mode

        # Test True cases
        for value in ["true", "True", "1", "yes"]:
            mock_getenv.return_value = value
            assert is_demo_mode() is True

        # Test False cases
        for value in ["false", "False", "0", "no", ""]:
            mock_getenv.return_value = value
            assert is_demo_mode() is False
