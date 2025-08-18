"""
Tests for the webserver components used by the Toga app.

This module tests the StaticFilesMiddleware and ThreadedWSGIServer classes
that handle static file serving for the embedded web application.
"""

# Check if toga is available using importlib
import importlib.util
import os
import tempfile

import pytest
from unittest.mock import Mock, patch

TOGA_AVAILABLE = importlib.util.find_spec("toga") is not None

# Skip all tests in this module if toga is not available
pytestmark = pytest.mark.skipif(not TOGA_AVAILABLE, reason="toga not available")

if TOGA_AVAILABLE:
    from stonks_overwatch.app.webserver import StaticFilesMiddleware, ThreadedWSGIServer
else:
    StaticFilesMiddleware = None
    ThreadedWSGIServer = None


class TestStaticFilesMiddleware:
    """Test cases for the StaticFilesMiddleware class."""

    @pytest.fixture
    def temp_static_dir(self):
        """Create a temporary directory with test static files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            css_file = os.path.join(temp_dir, "style.css")
            with open(css_file, "w") as f:
                f.write("body { color: red; }")

            js_file = os.path.join(temp_dir, "script.js")
            with open(js_file, "w") as f:
                f.write("console.log('test');")

            # Create subdirectory with file
            subdir = os.path.join(temp_dir, "images")
            os.makedirs(subdir)
            img_file = os.path.join(subdir, "logo.png")
            with open(img_file, "wb") as f:
                f.write(b"\x89PNG\r\n\x1a\n")  # PNG header

            yield temp_dir

    @pytest.fixture
    def mock_app(self):
        """Create a mock WSGI application."""
        app = Mock()
        app.return_value = [b"App response"]
        return app

    @pytest.fixture
    def middleware(self, mock_app, temp_static_dir):
        """Create StaticFilesMiddleware instance with test setup."""
        return StaticFilesMiddleware(app=mock_app, static_url="/static/", static_root=temp_static_dir)

    def test_initialization(self, mock_app, temp_static_dir):
        """Test middleware initialization with custom parameters."""
        middleware = StaticFilesMiddleware(app=mock_app, static_url="/assets/", static_root=temp_static_dir)

        assert middleware.app == mock_app
        assert middleware.static_url == "/assets/"
        assert middleware.static_root == temp_static_dir

    def test_initialization_defaults(self, mock_app):
        """Test middleware initialization with default parameters."""
        middleware = StaticFilesMiddleware(app=mock_app)

        assert middleware.app == mock_app
        assert middleware.static_url == "/static/"
        assert middleware.static_root == "staticfiles"

    def test_serve_css_file(self, middleware, temp_static_dir):
        """Test serving a CSS file."""
        environ = {"PATH_INFO": "/static/style.css"}
        start_response = Mock()

        response = middleware(environ, start_response)

        # Verify response headers
        start_response.assert_called_once_with("200 OK", [("Content-Type", "text/css")])

        # Verify file content is returned
        assert hasattr(response, "__iter__")  # FileWrapper object is iterable

    def test_serve_js_file(self, middleware, temp_static_dir):
        """Test serving a JavaScript file."""
        environ = {"PATH_INFO": "/static/script.js"}
        start_response = Mock()

        response = middleware(environ, start_response)

        # Verify response headers
        start_response.assert_called_once_with("200 OK", [("Content-Type", "text/javascript")])

        # Verify file content is returned
        assert hasattr(response, "__iter__")  # FileWrapper object is iterable

    def test_serve_png_file(self, middleware, temp_static_dir):
        """Test serving a PNG image file."""
        environ = {"PATH_INFO": "/static/images/logo.png"}
        start_response = Mock()

        response = middleware(environ, start_response)

        # Verify response headers
        start_response.assert_called_once_with("200 OK", [("Content-Type", "image/png")])

        # Verify file content is returned
        assert hasattr(response, "__iter__")  # FileWrapper object is iterable

    def test_serve_unknown_content_type(self, middleware, temp_static_dir):
        """Test serving a file with unknown content type."""
        # Create a file with unknown extension
        unknown_file = os.path.join(temp_static_dir, "test.unknown")
        with open(unknown_file, "w") as f:
            f.write("unknown content")

        environ = {"PATH_INFO": "/static/test.unknown"}
        start_response = Mock()

        middleware(environ, start_response)

        # Verify default content type is used
        start_response.assert_called_once_with("200 OK", [("Content-Type", "application/octet-stream")])

    def test_file_not_found(self, middleware):
        """Test handling of non-existent files."""
        environ = {"PATH_INFO": "/static/nonexistent.css"}
        start_response = Mock()

        result = middleware(environ, start_response)

        # Verify 404 response
        start_response.assert_called_once_with("404 Not Found", [("Content-Type", "text/plain")])

        # Verify error message
        assert result == [b"Static file not found"]

    def test_directory_path_blocked(self, middleware, temp_static_dir):
        """Test that directory paths are blocked (not served as files)."""
        environ = {"PATH_INFO": "/static/images/"}  # Directory path
        start_response = Mock()

        middleware(environ, start_response)

        # Verify 404 response (directories shouldn't be served)
        start_response.assert_called_once_with("404 Not Found", [("Content-Type", "text/plain")])

    def test_non_static_path_passes_through(self, middleware, mock_app):
        """Test that non-static paths are passed to the wrapped app."""
        environ = {"PATH_INFO": "/api/data"}
        start_response = Mock()

        result = middleware(environ, start_response)

        # Verify the wrapped app was called
        mock_app.assert_called_once_with(environ, start_response)
        assert result == [b"App response"]

    def test_root_path_passes_through(self, middleware, mock_app):
        """Test that root path is passed to the wrapped app."""
        environ = {"PATH_INFO": "/"}
        start_response = Mock()

        middleware(environ, start_response)

        # Verify the wrapped app was called
        mock_app.assert_called_once_with(environ, start_response)

    def test_empty_path_info(self, middleware, mock_app):
        """Test handling of empty PATH_INFO."""
        environ = {}  # No PATH_INFO
        start_response = Mock()

        middleware(environ, start_response)

        # Verify the wrapped app was called (empty path doesn't start with /static/)
        mock_app.assert_called_once_with(environ, start_response)

    def test_url_decoding(self, middleware, temp_static_dir):
        """Test that URL-encoded paths are properly decoded."""
        # Create file with space in name
        spaced_file = os.path.join(temp_static_dir, "spaced file.css")
        with open(spaced_file, "w") as f:
            f.write("body { margin: 0; }")

        # Request with URL-encoded space (%20)
        environ = {"PATH_INFO": "/static/spaced%20file.css"}
        start_response = Mock()

        middleware(environ, start_response)

        # Verify file is found and served
        start_response.assert_called_once_with("200 OK", [("Content-Type", "text/css")])

    def test_path_traversal_protection(self, middleware):
        """Test protection against path traversal attacks."""
        environ = {"PATH_INFO": "/static/../../../etc/passwd"}
        start_response = Mock()

        middleware(environ, start_response)

        # Should return 404 (file doesn't exist in static root)
        start_response.assert_called_once_with("404 Not Found", [("Content-Type", "text/plain")])

    @patch("builtins.open", side_effect=IOError("Permission denied"))
    def test_file_open_error(self, mock_open, middleware, temp_static_dir):
        """Test handling of file open errors."""
        environ = {"PATH_INFO": "/static/style.css"}
        start_response = Mock()

        # Mock os.path.exists to return True, but open() fails
        with patch("os.path.exists", return_value=True), patch("os.path.isfile", return_value=True):
            # Should raise the IOError since we can't handle it gracefully
            with pytest.raises(IOError):
                middleware(environ, start_response)


class TestThreadedWSGIServer:
    """Test cases for the ThreadedWSGIServer class."""

    def test_inheritance(self):
        """Test that ThreadedWSGIServer inherits from required base classes."""
        import socketserver
        from wsgiref.simple_server import WSGIServer

        assert issubclass(ThreadedWSGIServer, socketserver.ThreadingMixIn)
        assert issubclass(ThreadedWSGIServer, WSGIServer)

    def test_instantiation(self):
        """Test that ThreadedWSGIServer can be instantiated."""
        # We can't easily test the full server functionality without
        # starting an actual server, but we can verify the class exists
        # and can be imported/referenced
        assert ThreadedWSGIServer is not None
        assert hasattr(ThreadedWSGIServer, "__init__")

    def test_threaded_mixin_present(self):
        """Test that the ThreadingMixIn functionality is present."""
        import socketserver

        # Check that ThreadedWSGIServer has the threading capabilities
        assert hasattr(ThreadedWSGIServer, "daemon_threads")

        # Verify it's a proper subclass
        assert issubclass(ThreadedWSGIServer, socketserver.ThreadingMixIn)
