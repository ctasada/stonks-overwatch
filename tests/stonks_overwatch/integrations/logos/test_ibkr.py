from stonks_overwatch.integrations.logos.ibkr import IbkrLogoIntegration

from django.test import TestCase


class TestIbkrLogoIntegration(TestCase):
    """Tests for IbkrLogoIntegration."""

    def setUp(self):
        self.integration = IbkrLogoIntegration()

    def test_get_logo_url_returns_url_for_valid_conid(self):
        """Valid numeric conid produces a non-empty URL."""
        url = self.integration.get_logo_url(conid="12345")
        self.assertTrue(url.startswith(IbkrLogoIntegration.BASE_URL))
        self.assertIn("conid=12345", url)

    def test_get_logo_url_default_theme_is_light(self):
        """Default theme produces mark_light icon type."""
        url = self.integration.get_logo_url(conid="12345")
        self.assertIn("mark_light", url)

    def test_get_logo_url_dark_theme(self):
        """Dark theme produces mark_dark icon type."""
        url = self.integration.get_logo_url(conid="12345", theme="dark")
        self.assertIn("mark_dark", url)

    def test_get_logo_url_returns_empty_for_non_digit_conid(self):
        """Non-digit conid returns empty string."""
        self.assertEqual(self.integration.get_logo_url(conid="abc"), "")

    def test_get_logo_url_returns_empty_for_alphanumeric_conid(self):
        """Alphanumeric conid (mixed digits and letters) returns empty string."""
        self.assertEqual(self.integration.get_logo_url(conid="123abc"), "")

    def test_get_logo_url_returns_empty_for_empty_conid(self):
        """Empty conid returns empty string."""
        self.assertEqual(self.integration.get_logo_url(conid=""), "")

    def test_get_logo_url_returns_empty_for_none_conid(self):
        """None conid returns empty string."""
        self.assertEqual(self.integration.get_logo_url(conid=None), "")

    def test_get_logo_url_dark_theme_uppercase(self):
        """Uppercase DARK theme is treated the same as lowercase dark."""
        url = self.integration.get_logo_url(conid="12345", theme="DARK")
        self.assertIn("mark_dark", url)

    def test_get_logo_url_unknown_theme_defaults_to_light(self):
        """Unrecognised theme value falls through to mark_light."""
        url = self.integration.get_logo_url(conid="12345", theme="invalid")
        self.assertIn("mark_light", url)

    def test_get_logo_url_none_theme_defaults_to_light(self):
        """None theme falls through to mark_light."""
        url = self.integration.get_logo_url(conid="12345", theme=None)
        self.assertIn("mark_light", url)

    def test_get_logo_url_contains_expected_query_params(self):
        """URL contains all expected query parameters."""
        url = self.integration.get_logo_url(conid="99999")
        self.assertIn("conid=99999", url)
        self.assertIn("type=mark_light", url)
        self.assertIn("scale=200x200", url)
        self.assertIn("composite_auto=false", url)
        self.assertIn("composite_radius=0", url)
