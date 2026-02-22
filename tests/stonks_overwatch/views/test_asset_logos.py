from django.http import HttpResponse, HttpResponseNotFound

from stonks_overwatch.integrations.logos.ibkr import IbkrLogoIntegration
from stonks_overwatch.integrations.logos.logodev import LogoDevIntegration
from stonks_overwatch.views.asset_logos import AssetLogoView, LogoType

from django.test import RequestFactory, TestCase
from unittest.mock import MagicMock, patch


class TestLogoType(TestCase):
    """Tests for the LogoType enum."""

    def test_from_str_valid_types(self):
        """Test converting valid strings to LogoType."""
        test_cases = [
            ("stock", LogoType.STOCK),
            ("etf", LogoType.ETF),
            ("cash", LogoType.CASH),
            ("crypto", LogoType.CRYPTO),
            ("country", LogoType.COUNTRY),
            ("sector", LogoType.SECTOR),
        ]

        for input_str, expected_type in test_cases:
            with self.subTest(input_str=input_str):
                result = LogoType.from_str(input_str)
                self.assertEqual(result, expected_type)

    def test_from_str_invalid_type(self):
        """Test converting invalid string to LogoType."""
        result = LogoType.from_str("invalid_type")
        self.assertEqual(result, LogoType.UNKNOWN)

    def test_from_str_case_insensitive(self):
        """Test that string conversion is case insensitive."""
        test_cases = [
            ("STOCK", LogoType.STOCK),
            ("Etf", LogoType.ETF),
            ("Cash", LogoType.CASH),
            ("CRYPTO", LogoType.CRYPTO),
        ]

        for input_str, expected_type in test_cases:
            with self.subTest(input_str=input_str):
                result = LogoType.from_str(input_str)
                self.assertEqual(result, expected_type)


class TestAssetLogoView(TestCase):
    """Tests for the AssetLogoView class."""

    def setUp(self):
        """Set up a test environment."""
        self.factory = RequestFactory()
        self.view = AssetLogoView()

    def test_get_invalid_product_type(self):
        """Test getting logo for an invalid product type."""
        request = self.factory.get("/assets/invalid/appl")
        response = self.view.get(request, product_type="invalid", symbol="appl")
        self.assertIsInstance(response, HttpResponseNotFound)
        self.assertEqual(response.content.decode(), "Invalid product type")

    @patch("stonks_overwatch.integrations.logos.registry.LogoIntegrationRegistry.get_active_integrations")
    def test_get_uses_logodev_before_ibkr(self, mock_registry):
        """Logo.dev should be preferred, then IBKR, then fallback."""
        logodev = MagicMock(spec=LogoDevIntegration)
        logodev.supports.return_value = True
        logodev.get_logo_url.return_value = "https://logo.dev/logo.png"

        ibkr = MagicMock(spec=IbkrLogoIntegration)
        ibkr.supports.return_value = True
        ibkr.get_logo_url.return_value = "https://ibkr/logo.png"

        mock_registry.return_value = [logodev, ibkr]

        request = self.factory.get("/assets/stock/appl")
        response = self.view.get(request, product_type="stock", symbol="appl")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://logo.dev/logo.png")
        logodev.get_logo_url.assert_called_once()
        ibkr.get_logo_url.assert_not_called()

    @patch("stonks_overwatch.integrations.logos.registry.LogoIntegrationRegistry.get_active_integrations")
    def test_get_falls_back_to_ibkr_when_logodev_missing(self, mock_registry):
        """If Logo.dev has no logo, IBKR should be used when enabled."""
        logodev = MagicMock(spec=LogoDevIntegration)
        logodev.supports.return_value = True
        logodev.get_logo_url.return_value = ""

        ibkr = MagicMock(spec=IbkrLogoIntegration)
        ibkr.supports.return_value = True
        ibkr.get_logo_url.return_value = "https://ibkr/logo.png"

        mock_registry.return_value = [logodev, ibkr]

        request = self.factory.get("/assets/stock/appl")
        response = self.view.get(request, product_type="stock", symbol="appl")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://ibkr/logo.png")
        logodev.get_logo_url.assert_called_once()
        ibkr.get_logo_url.assert_called_once()

    @patch("requests.get")
    @patch("stonks_overwatch.integrations.logos.registry.LogoIntegrationRegistry.get_active_integrations")
    def test_get_falls_back_to_default_when_no_integrations(self, mock_registry, mock_get):
        """When no integrations return a logo, fall back to the default URL."""
        logodev = MagicMock(spec=LogoDevIntegration)
        logodev.supports.return_value = True
        logodev.get_logo_url.return_value = ""

        ibkr = MagicMock(spec=IbkrLogoIntegration)
        ibkr.supports.return_value = True
        ibkr.get_logo_url.return_value = ""

        mock_registry.return_value = [logodev, ibkr]

        mock_response = MagicMock()
        mock_response.content = b"<svg>test</svg>"
        mock_response.headers = {"Content-Type": "image/svg+xml"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        request = self.factory.get("/assets/stock/appl")
        response = self.view.get(request, product_type="stock", symbol="appl")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"<svg>test</svg>")
        mock_get.assert_called_once_with("https://logos.stockanalysis.com/appl.svg", timeout=5)

    @patch("stonks_overwatch.integrations.logos.registry.LogoIntegrationRegistry.get_active_integrations")
    def test_get_skips_invalid_conid(self, mock_registry):
        """Invalid conid should be ignored and still attempt integrations."""
        logodev = MagicMock(spec=LogoDevIntegration)
        logodev.supports.return_value = True
        logodev.get_logo_url.return_value = "https://logo.dev/logo.png"

        mock_registry.return_value = [logodev]

        request = self.factory.get("/assets/stock/appl?conid=abc")
        response = self.view.get(request, product_type="stock", symbol="appl")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://logo.dev/logo.png")
        logodev.get_logo_url.assert_called_once()

    @patch("requests.get")
    def test_get_stock_logo(self, mock_get):
        """Test getting stock logo."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.content = b"<svg>test</svg>"
        mock_response.headers = {"Content-Type": "image/svg+xml"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        request = self.factory.get("/assets/stock/appl")
        response = self.view.get(request, product_type="stock", symbol="appl")

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.content, b"<svg>test</svg>")
        self.assertEqual(response["Content-Type"], "image/svg+xml")
        mock_get.assert_called_once_with("https://logos.stockanalysis.com/appl.svg", timeout=5)

    @patch("requests.get")
    def test_get_crypto_logo(self, mock_get):
        """Test getting crypto logo."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.content = b"<svg>test</svg>"
        mock_response.headers = {"Content-Type": "image/svg+xml"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        request = self.factory.get("/assets/crypto/btc")
        response = self.view.get(request, product_type="crypto", symbol="btc")

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.content, b"<svg>test</svg>")
        self.assertEqual(response["Content-Type"], "image/svg+xml")
        mock_get.assert_called_once_with(
            "https://raw.githubusercontent.com/Cryptofonts/cryptoicons/master/SVG/btc.svg", timeout=5
        )

    def test_get_cash_logo(self):
        """Test getting cash logo."""
        request = self.factory.get("/assets/cash/eur")
        response = self.view.get(request, product_type="cash", symbol="eur")

        self.assertIsInstance(response, HttpResponse)
        self.assertIn("<svg", response.content.decode("utf-8"))
        self.assertIn("€", response.content.decode("utf-8"))
        self.assertEqual(response["Content-Type"], "image/svg+xml")

    @patch("requests.get")
    def test_get_country_logo(self, mock_get):
        """Test getting country logo."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.content = b"<svg>test</svg>"
        mock_response.headers = {"Content-Type": "image/svg+xml"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        request = self.factory.get("/assets/country/🇺🇸")
        response = self.view.get(request, product_type="country", symbol="🇺🇸")

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.content, b"<svg>test</svg>")
        self.assertEqual(response["Content-Type"], "image/svg+xml")
        mock_get.assert_called_once_with(
            "https://cdn.jsdelivr.net/gh/jdecked/twemoji@latest/assets/svg/1f1fa-1f1f8.svg", timeout=5
        )

    @patch("requests.get")
    def test_get_sector_logo(self, mock_get):
        """Test getting sector logo."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.content = b"<svg>test</svg>"
        mock_response.headers = {"Content-Type": "image/svg+xml"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        request = self.factory.get("/assets/sector/🖥️")
        response = self.view.get(request, product_type="sector", symbol="🖥️")

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.content, b"<svg>test</svg>")
        self.assertEqual(response["Content-Type"], "image/svg+xml")
        mock_get.assert_called_once_with(
            "https://cdn.jsdelivr.net/gh/jdecked/twemoji@latest/assets/svg/1f5a5-fe0f.svg", timeout=5
        )

    @patch("requests.get")
    def test_get_logo_not_found(self, mock_get):
        """Test getting logo when an external service fails."""
        # Mock the failed response by raising RequestException
        from requests.exceptions import RequestException

        mock_get.side_effect = RequestException("Failed to fetch logo")

        request = self.factory.get("/assets/stock/appl")
        response = self.view.get(request, product_type="stock", symbol="appl")

        self.assertIsInstance(response, HttpResponse)
        self.assertIn(b"<svg", response.content)
        self.assertIn(b"APPL", response.content)
        self.assertEqual(response["Content-Type"], "image/svg+xml")
        mock_get.assert_called_once_with("https://logos.stockanalysis.com/appl.svg", timeout=5)

    def test_generate_symbol(self):
        """Test generating symbol SVG."""
        symbol = "TEST"
        svg = self.view._AssetLogoView__generate_symbol(symbol)

        self.assertIn(b"<svg", svg.encode())
        self.assertIn(b"TEST", svg.encode())
        self.assertIn(b"font-size", svg.encode())

    def test_emoji_to_svg(self):
        """Test converting emoji to SVG URL."""
        # Test with a country flag emoji (🇺🇸)
        emoji = "🇺🇸"
        url = self.view._AssetLogoView__emoji_to_svg(emoji)
        self.assertEqual(url, "https://cdn.jsdelivr.net/gh/jdecked/twemoji@latest/assets/svg/1f1fa-1f1f8.svg")

        # Test with a sector emoji (🖥️)
        emoji = "🖥️"
        url = self.view._AssetLogoView__emoji_to_svg(emoji)
        self.assertEqual(url, "https://cdn.jsdelivr.net/gh/jdecked/twemoji@latest/assets/svg/1f5a5-fe0f.svg")


class TestAssetLogoViewIbkr(TestCase):
    """Tests for IBKR logo paths in AssetLogoView."""

    def setUp(self):
        self.factory = RequestFactory()
        self.view = AssetLogoView()

    @patch("stonks_overwatch.integrations.logos.registry.LogoIntegrationRegistry.get_active_integrations")
    def test_get_stock_logo_with_conid_redirects_to_ibkr(self, mock_registry):
        """Valid conid on a stock request redirects to the IBKR logo URL."""
        ibkr_url = "https://www.interactivebrokers.ie/tws.proxy/public/icons/benzinga?conid=12345&type=mark_light"
        ibkr = MagicMock(spec=IbkrLogoIntegration)
        ibkr.supports.return_value = True
        ibkr.get_logo_url.return_value = ibkr_url
        mock_registry.return_value = [ibkr]

        request = self.factory.get("/assets/stock/aapl", {"conid": "12345"})
        response = self.view.get(request, product_type="stock", symbol="aapl")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], ibkr_url)
        ibkr.get_logo_url.assert_called_once()

    @patch("stonks_overwatch.integrations.logos.registry.LogoIntegrationRegistry.get_active_integrations")
    def test_get_etf_logo_with_conid_redirects_to_ibkr(self, mock_registry):
        """Valid conid on an ETF request redirects to the IBKR logo URL."""
        ibkr_url = "https://www.interactivebrokers.ie/tws.proxy/public/icons/benzinga?conid=99999&type=mark_light"
        ibkr = MagicMock(spec=IbkrLogoIntegration)
        ibkr.supports.return_value = True
        ibkr.get_logo_url.return_value = ibkr_url
        mock_registry.return_value = [ibkr]

        request = self.factory.get("/assets/etf/spy", {"conid": "99999"})
        response = self.view.get(request, product_type="etf", symbol="spy")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], ibkr_url)

    @patch("requests.get")
    @patch("stonks_overwatch.integrations.logos.registry.LogoIntegrationRegistry.get_active_integrations")
    def test_get_stock_logo_with_conid_falls_back_to_cdn_when_ibkr_returns_empty(self, mock_registry, mock_get):
        """When IBKR returns no URL, the request falls back to the CDN."""
        ibkr = MagicMock(spec=IbkrLogoIntegration)
        ibkr.supports.return_value = True
        ibkr.get_logo_url.return_value = ""
        mock_registry.return_value = [ibkr]

        mock_response = MagicMock()
        mock_response.content = b"<svg>test</svg>"
        mock_response.headers = {"Content-Type": "image/svg+xml"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        request = self.factory.get("/assets/stock/aapl", {"conid": "12345"})
        response = self.view.get(request, product_type="stock", symbol="aapl")

        self.assertIsInstance(response, HttpResponse)
        mock_get.assert_called_once_with("https://logos.stockanalysis.com/aapl.svg", timeout=5)

    @patch("requests.get")
    @patch("stonks_overwatch.integrations.logos.registry.LogoIntegrationRegistry.get_active_integrations")
    def test_get_stock_logo_without_conid_passes_empty_conid_to_ibkr(self, mock_registry, mock_get):
        """Requests without conid pass conid='' to integrations (IBKR will return '' for it)."""
        ibkr = MagicMock(spec=IbkrLogoIntegration)
        ibkr.supports.return_value = True
        ibkr.get_logo_url.return_value = ""
        mock_registry.return_value = [ibkr]

        mock_response = MagicMock()
        mock_response.content = b"<svg>test</svg>"
        mock_response.headers = {"Content-Type": "image/svg+xml"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        request = self.factory.get("/assets/stock/aapl")
        self.view.get(request, product_type="stock", symbol="aapl")

        _, kwargs = ibkr.get_logo_url.call_args
        self.assertEqual(kwargs.get("conid", ""), "")

    @patch("requests.get")
    @patch("stonks_overwatch.integrations.logos.registry.LogoIntegrationRegistry.get_active_integrations")
    def test_get_stock_logo_with_invalid_conid_passes_empty_conid(self, mock_registry, mock_get):
        """Non-digit conid is sanitized to '' before being passed to integrations."""
        ibkr = MagicMock(spec=IbkrLogoIntegration)
        ibkr.supports.return_value = True
        ibkr.get_logo_url.return_value = ""
        mock_registry.return_value = [ibkr]

        mock_response = MagicMock()
        mock_response.content = b"<svg>test</svg>"
        mock_response.headers = {"Content-Type": "image/svg+xml"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        request = self.factory.get("/assets/stock/aapl", {"conid": "not-a-number"})
        response = self.view.get(request, product_type="stock", symbol="aapl")

        self.assertIsInstance(response, HttpResponse)
        _, kwargs = ibkr.get_logo_url.call_args
        self.assertEqual(kwargs.get("conid", ""), "")

    @patch("requests.get")
    @patch("stonks_overwatch.integrations.logos.registry.LogoIntegrationRegistry.get_active_integrations")
    def test_get_crypto_logo_with_conid_skips_ibkr(self, mock_registry, mock_get):
        """conid is ignored for crypto (not STOCK or ETF); IBKR integration is not called."""
        ibkr = MagicMock(spec=IbkrLogoIntegration)
        ibkr.supports.return_value = False
        mock_registry.return_value = [ibkr]

        mock_response = MagicMock()
        mock_response.content = b"<svg>test</svg>"
        mock_response.headers = {"Content-Type": "image/svg+xml"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        request = self.factory.get("/assets/crypto/btc", {"conid": "12345"})
        self.view.get(request, product_type="crypto", symbol="btc")

        ibkr.get_logo_url.assert_not_called()
