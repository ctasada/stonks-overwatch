from django.http import HttpResponse, HttpResponseNotFound

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
        request = self.factory.get('/assets/invalid/appl')
        response = self.view.get(request, product_type="invalid", symbol="appl")
        self.assertIsInstance(response, HttpResponseNotFound)
        self.assertEqual(response.content.decode(), "Invalid product type")

    @patch('requests.get')
    def test_get_stock_logo(self, mock_get):
        """Test getting stock logo."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.content = b'<svg>test</svg>'
        mock_response.headers = {'Content-Type': 'image/svg+xml'}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        request = self.factory.get('/assets/stock/appl')
        response = self.view.get(request, product_type="stock", symbol="appl")

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.content, b'<svg>test</svg>')
        self.assertEqual(response['Content-Type'], 'image/svg+xml')
        mock_get.assert_called_once_with(
            "https://logos.stockanalysis.com/appl.svg",
            timeout=5
        )

    @patch('requests.get')
    def test_get_crypto_logo(self, mock_get):
        """Test getting crypto logo."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.content = b'<svg>test</svg>'
        mock_response.headers = {'Content-Type': 'image/svg+xml'}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        request = self.factory.get('/assets/crypto/btc')
        response = self.view.get(request, product_type="crypto", symbol="btc")

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.content, b'<svg>test</svg>')
        self.assertEqual(response['Content-Type'], 'image/svg+xml')
        mock_get.assert_called_once_with(
            "https://raw.githubusercontent.com/Cryptofonts/cryptoicons/master/SVG/btc.svg",
            timeout=5
        )

    def test_get_cash_logo(self):
        """Test getting cash logo."""
        request = self.factory.get('/assets/cash/eur')
        response = self.view.get(request, product_type="cash", symbol="eur")

        self.assertIsInstance(response, HttpResponse)
        self.assertIn('<svg', response.content.decode('utf-8'))
        self.assertIn('€', response.content.decode('utf-8'))
        self.assertEqual(response['Content-Type'], 'image/svg+xml')

    @patch('requests.get')
    def test_get_country_logo(self, mock_get):
        """Test getting country logo."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.content = b'<svg>test</svg>'
        mock_response.headers = {'Content-Type': 'image/svg+xml'}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        request = self.factory.get('/assets/country/🇺🇸')
        response = self.view.get(request, product_type="country", symbol="🇺🇸")

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.content, b'<svg>test</svg>')
        self.assertEqual(response['Content-Type'], 'image/svg+xml')
        mock_get.assert_called_once_with(
            "https://cdnjs.cloudflare.com/ajax/libs/twemoji/16.0.1/svg/1f1fa-1f1f8.svg",
            timeout=5
        )

    @patch('requests.get')
    def test_get_sector_logo(self, mock_get):
        """Test getting sector logo."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.content = b'<svg>test</svg>'
        mock_response.headers = {'Content-Type': 'image/svg+xml'}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        request = self.factory.get('/assets/sector/🖥️')
        response = self.view.get(request, product_type="sector", symbol="🖥️")

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.content, b'<svg>test</svg>')
        self.assertEqual(response['Content-Type'], 'image/svg+xml')
        mock_get.assert_called_once_with(
            "https://cdnjs.cloudflare.com/ajax/libs/twemoji/16.0.1/svg/1f5a5-fe0f.svg",
            timeout=5
        )

    @patch('requests.get')
    def test_get_logo_not_found(self, mock_get):
        """Test getting logo when an external service fails."""
        # Mock the failed response by raising RequestException
        from requests.exceptions import RequestException
        mock_get.side_effect = RequestException("Failed to fetch logo")

        request = self.factory.get('/assets/stock/appl')
        response = self.view.get(request, product_type="stock", symbol="appl")

        self.assertIsInstance(response, HttpResponse)
        self.assertIn(b'<svg', response.content)
        self.assertIn(b'APPL', response.content)
        self.assertEqual(response['Content-Type'], 'image/svg+xml')
        mock_get.assert_called_once_with(
            "https://logos.stockanalysis.com/appl.svg",
            timeout=5
        )

    def test_generate_symbol(self):
        """Test generating symbol SVG."""
        symbol = "TEST"
        svg = self.view._AssetLogoView__generate_symbol(symbol)

        self.assertIn(b'<svg', svg.encode())
        self.assertIn(b'TEST', svg.encode())
        self.assertIn(b'font-size', svg.encode())

    def test_emoji_to_svg(self):
        """Test converting emoji to SVG URL."""
        # Test with a country flag emoji (🇺🇸)
        emoji = "🇺🇸"
        url = self.view._AssetLogoView__emoji_to_svg(emoji)
        self.assertEqual(
            url,
            "https://cdnjs.cloudflare.com/ajax/libs/twemoji/16.0.1/svg/1f1fa-1f1f8.svg"
        )

        # Test with a sector emoji (🖥️)
        emoji = "🖥️"
        url = self.view._AssetLogoView__emoji_to_svg(emoji)
        self.assertEqual(
            url,
            "https://cdnjs.cloudflare.com/ajax/libs/twemoji/16.0.1/svg/1f5a5-fe0f.svg"
        )
