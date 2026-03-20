from requests.exceptions import ConnectionError

from stonks_overwatch.integrations.logos.ibkr import IbkrLogoIntegration
from stonks_overwatch.integrations.logos.types import LogoType

from django.test import TestCase
from unittest.mock import patch


class DummyResponse:
    def __init__(self, status_code: int = 200):
        self.status_code = status_code
        self.ok = status_code < 400

    def close(self) -> None:
        return None


class TestIbkrLogoIntegration(TestCase):
    """Tests for IbkrLogoIntegration."""

    def setUp(self):
        self.integration = IbkrLogoIntegration()

    @patch("stonks_overwatch.integrations.logos.ibkr.requests.get", return_value=DummyResponse(200))
    def test_get_logo_url_returns_url_for_valid_conid(self, _mock):
        """Valid numeric conid produces a non-empty URL."""
        _mock.return_value.status_code = 200
        _mock.return_value.ok = True
        url = self.integration.get_logo_url(LogoType.STOCK, "AAPL", conid="12345")
        self.assertTrue(url.startswith(IbkrLogoIntegration.BASE_URL))
        self.assertIn("conid=12345", url)

    @patch("stonks_overwatch.integrations.logos.ibkr.requests.get", return_value=DummyResponse(200))
    def test_get_logo_url_default_theme_is_light(self, _mock):
        """Default theme produces mark_light icon type."""
        _mock.return_value.status_code = 200
        _mock.return_value.ok = True
        url = self.integration.get_logo_url(LogoType.STOCK, "AAPL", conid="12345")
        self.assertIn("mark_light", url)

    @patch("stonks_overwatch.integrations.logos.ibkr.requests.get", return_value=DummyResponse(200))
    def test_get_logo_url_dark_theme(self, _mock):
        """Dark theme produces mark_dark icon type."""
        _mock.return_value.status_code = 200
        _mock.return_value.ok = True
        url = self.integration.get_logo_url(LogoType.STOCK, "AAPL", conid="12345", theme="dark")
        self.assertIn("mark_dark", url)

    def test_get_logo_url_returns_empty_for_non_digit_conid(self):
        """Non-digit conid returns empty string."""
        self.assertEqual(self.integration.get_logo_url(LogoType.STOCK, "AAPL", conid="abc"), "")

    def test_get_logo_url_returns_empty_for_alphanumeric_conid(self):
        """Alphanumeric conid (mixed digits and letters) returns empty string."""
        self.assertEqual(self.integration.get_logo_url(LogoType.STOCK, "AAPL", conid="123abc"), "")

    def test_get_logo_url_returns_empty_for_empty_conid(self):
        """Empty conid returns empty string."""
        self.assertEqual(self.integration.get_logo_url(LogoType.STOCK, "AAPL", conid=""), "")

    def test_get_logo_url_returns_empty_for_none_conid(self):
        """None conid returns empty string."""
        self.assertEqual(self.integration.get_logo_url(LogoType.STOCK, "AAPL", conid=None), "")

    @patch("stonks_overwatch.integrations.logos.ibkr.requests.get", return_value=DummyResponse(200))
    def test_get_logo_url_dark_theme_uppercase(self, _mock):
        """Uppercase DARK theme is treated the same as lowercase dark."""
        _mock.return_value.status_code = 200
        _mock.return_value.ok = True
        url = self.integration.get_logo_url(LogoType.STOCK, "AAPL", conid="12345", theme="DARK")
        self.assertIn("mark_dark", url)

    @patch("stonks_overwatch.integrations.logos.ibkr.requests.get", return_value=DummyResponse(200))
    def test_get_logo_url_unknown_theme_defaults_to_light(self, _mock):
        """Unrecognised theme value falls through to mark_light."""
        _mock.return_value.status_code = 200
        _mock.return_value.ok = True
        url = self.integration.get_logo_url(LogoType.STOCK, "AAPL", conid="12345", theme="invalid")
        self.assertIn("mark_light", url)

    @patch("stonks_overwatch.integrations.logos.ibkr.requests.get", return_value=DummyResponse(200))
    def test_get_logo_url_contains_expected_query_params(self, _mock):
        """URL contains all expected query parameters."""
        _mock.return_value.status_code = 200
        _mock.return_value.ok = True
        url = self.integration.get_logo_url(LogoType.STOCK, "AAPL", conid="99999")
        self.assertIn("conid=99999", url)
        self.assertIn("type=mark_light", url)
        self.assertIn("scale=200x200", url)
        self.assertIn("composite_auto=false", url)
        self.assertIn("composite_radius=0", url)

    @patch("stonks_overwatch.integrations.logos.ibkr.requests.get", return_value=DummyResponse(404))
    def test_get_logo_url_returns_empty_on_404(self, _mock):
        """HTTP 404 from the Benzinga proxy returns empty string."""
        _mock.return_value.status_code = 404
        _mock.return_value.ok = False
        self.assertEqual(self.integration.get_logo_url(LogoType.STOCK, "AAPL", conid="40404"), "")

    @patch("stonks_overwatch.integrations.logos.ibkr.requests.get", return_value=DummyResponse(500))
    def test_get_logo_url_returns_empty_on_server_error(self, _mock):
        """HTTP 5xx from the Benzinga proxy returns empty string."""
        _mock.return_value.status_code = 500
        _mock.return_value.ok = False
        self.assertEqual(self.integration.get_logo_url(LogoType.STOCK, "AAPL", conid="50500"), "")

    @patch("stonks_overwatch.integrations.logos.ibkr.requests.get", side_effect=ConnectionError("timeout"))
    def test_get_logo_url_returns_empty_on_request_exception(self, _mock):
        """Network error during the Benzinga request returns empty string."""
        self.assertEqual(self.integration.get_logo_url(LogoType.STOCK, "AAPL", conid="11111"), "")
