import os
import tempfile

from django.conf import settings
from django.http import FileResponse, Http404

from stonks_overwatch.views.static import RootStaticFileView

from django.test import RequestFactory, TestCase
from unittest.mock import patch


class TestRootStaticFileView(TestCase):
    """Tests for the RootStaticFileView class."""

    def setUp(self):
        """Set up a test environment."""
        self.factory = RequestFactory()
        self.view = RootStaticFileView()

        # Create a temporary directory for test static files
        self.temp_dir = tempfile.mkdtemp()
        self.original_static_root = settings.STATIC_ROOT
        settings.STATIC_ROOT = self.temp_dir

    def tearDown(self):
        """Clean up the test environment."""
        # Clean up test files
        for filename in os.listdir(self.temp_dir):
            file_path = os.path.join(self.temp_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

        # Restore original STATIC_ROOT
        settings.STATIC_ROOT = self.original_static_root

        # Remove the temporary directory
        try:
            os.rmdir(self.temp_dir)
        except Exception as e:
            print(f"Error removing directory {self.temp_dir}: {e}")

    def test_get_existing_file(self):
        """Test getting an existing static file."""
        # Create a test file
        test_file_path = os.path.join(self.temp_dir, "favicon.ico")
        with open(test_file_path, "wb") as f:
            f.write(b"test content")

        request = self.factory.get("/favicon.ico")
        response = self.view.get(request, filename="favicon.ico")

        self.assertIsInstance(response, FileResponse)
        self.assertEqual(response.status_code, 200)
        self.assertIn(response["Content-Type"], ["image/x-icon", "image/vnd.microsoft.icon"])

    def test_get_nonexistent_file(self):
        """Test getting a non-existent static file."""
        request = self.factory.get("/nonexistent.ico")
        with self.assertRaises(Http404):
            self.view.get(request, filename="nonexistent.ico")

    def test_get_apple_touch_icon(self):
        """Test getting apple touch icon."""
        # Create a test file
        test_file_path = os.path.join(self.temp_dir, "apple-touch-icon.png")
        with open(test_file_path, "wb") as f:
            f.write(b"test content")

        request = self.factory.get("/apple-touch-icon.png")
        response = self.view.get(request, filename="apple-touch-icon.png")

        self.assertIsInstance(response, FileResponse)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")

    def test_get_apple_touch_icon_precomposed(self):
        """Test getting precomposed apple touch icon."""
        # Create a test file
        test_file_path = os.path.join(self.temp_dir, "apple-touch-icon-precomposed.png")
        with open(test_file_path, "wb") as f:
            f.write(b"test content")

        request = self.factory.get("/apple-touch-icon-precomposed.png")
        response = self.view.get(request, filename="apple-touch-icon-precomposed.png")

        self.assertIsInstance(response, FileResponse)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")

    @patch("os.path.exists")
    def test_file_not_found(self, mock_exists):
        """Test handling of file not found error."""
        mock_exists.return_value = False
        request = self.factory.get("/favicon.ico")

        with self.assertRaises(Http404) as context:
            self.view.get(request, filename="favicon.ico")

        self.assertEqual(str(context.exception), "favicon.ico not found.")
