"""
Tests for dialog utility functions.

This module tests utility functions used by dialogs in the Toga app,
particularly window positioning and centering functionality.
"""

from stonks_overwatch.app.utils.dialog_utils import center_window_on_parent

import pytest
from unittest.mock import MagicMock, patch


class TestCenterWindowOnParent:
    """Test cases for the center_window_on_parent function."""

    @pytest.fixture
    def mock_window(self):
        """Create a mock Toga window."""
        window = MagicMock()
        window.size = (400, 300)  # Default dialog size
        return window

    @pytest.fixture
    def mock_parent_window(self):
        """Create a mock parent Toga window."""
        parent = MagicMock()
        parent.position = (100, 50)  # Parent position
        parent.size = (1200, 800)  # Parent size
        return parent

    def test_center_window_on_valid_parent(self, mock_window, mock_parent_window):
        """Test centering a window on a valid parent window."""
        center_window_on_parent(mock_window, mock_parent_window)

        # Calculate expected position
        # Parent: position=(100, 50), size=(1200, 800)
        # Dialog: size=(400, 300)
        # Expected: x = 100 + (1200 - 400) // 2 = 100 + 400 = 500
        #          y = 50 + (800 - 300) // 2 = 50 + 250 = 300
        expected_x = 100 + (1200 - 400) // 2  # 500
        expected_y = 50 + (800 - 300) // 2  # 300

        mock_window.position = (expected_x, expected_y)
        assert mock_window.position == (500, 300)

    def test_center_window_with_none_parent(self, mock_window):
        """Test centering when parent window is None."""
        original_position = getattr(mock_window, "position", None)

        center_window_on_parent(mock_window, None)

        # Window position should not be modified when parent is None
        assert getattr(mock_window, "position", None) == original_position

    def test_center_window_parent_no_position(self, mock_window):
        """Test centering when parent window has no position attribute."""
        parent = MagicMock()
        parent.size = (1200, 800)
        del parent.position  # Remove position attribute

        original_position = getattr(mock_window, "position", None)

        center_window_on_parent(mock_window, parent)

        # Window position should not be modified when parent has no position
        assert getattr(mock_window, "position", None) == original_position

    def test_center_window_parent_no_size(self, mock_window):
        """Test centering when parent window has no size attribute."""
        parent = MagicMock()
        parent.position = (100, 50)
        del parent.size  # Remove size attribute

        original_position = getattr(mock_window, "position", None)

        center_window_on_parent(mock_window, parent)

        # Window position should not be modified when parent has no size
        assert getattr(mock_window, "position", None) == original_position

    def test_center_window_parent_none_position(self, mock_window):
        """Test centering when parent window position is None."""
        parent = MagicMock()
        parent.position = None
        parent.size = (1200, 800)

        original_position = getattr(mock_window, "position", None)

        center_window_on_parent(mock_window, parent)

        # Window position should not be modified when parent position is None
        assert getattr(mock_window, "position", None) == original_position

    def test_center_window_parent_none_size(self, mock_window):
        """Test centering when parent window size is None."""
        parent = MagicMock()
        parent.position = (100, 50)
        parent.size = None

        original_position = getattr(mock_window, "position", None)

        center_window_on_parent(mock_window, parent)

        # Window position should not be modified when parent size is None
        assert getattr(mock_window, "position", None) == original_position

    def test_center_small_dialog_on_large_parent(self, mock_parent_window):
        """Test centering a small dialog on a large parent window."""
        small_dialog = MagicMock()
        small_dialog.size = (200, 150)

        center_window_on_parent(small_dialog, mock_parent_window)

        # Calculate expected position for small dialog
        # Parent: position=(100, 50), size=(1200, 800)
        # Dialog: size=(200, 150)
        expected_x = 100 + (1200 - 200) // 2  # 600
        expected_y = 50 + (800 - 150) // 2  # 375

        small_dialog.position = (expected_x, expected_y)
        assert small_dialog.position == (600, 375)

    def test_center_large_dialog_on_small_parent(self):
        """Test centering a large dialog on a small parent window."""
        large_dialog = MagicMock()
        large_dialog.size = (1000, 700)

        small_parent = MagicMock()
        small_parent.position = (50, 25)
        small_parent.size = (600, 400)

        center_window_on_parent(large_dialog, small_parent)

        # Calculate expected position for large dialog
        # Even if dialog is larger than parent, calculation should work
        # Parent: position=(50, 25), size=(600, 400)
        # Dialog: size=(1000, 700)
        expected_x = 50 + (600 - 1000) // 2  # -150
        expected_y = 25 + (400 - 700) // 2  # -125

        large_dialog.position = (expected_x, expected_y)
        assert large_dialog.position == (-150, -125)

    def test_center_window_zero_size_parent(self, mock_window):
        """Test centering when parent window has zero size."""
        parent = MagicMock()
        parent.position = (100, 50)
        parent.size = (0, 0)

        center_window_on_parent(mock_window, parent)

        # Calculate expected position
        # Parent: position=(100, 50), size=(0, 0)
        # Dialog: size=(400, 300)
        expected_x = 100 + (0 - 400) // 2  # -100
        expected_y = 50 + (0 - 300) // 2  # -100

        mock_window.position = (expected_x, expected_y)
        assert mock_window.position == (-100, -100)

    def test_center_window_zero_size_dialog(self, mock_parent_window):
        """Test centering when dialog window has zero size."""
        zero_dialog = MagicMock()
        zero_dialog.size = (0, 0)

        center_window_on_parent(zero_dialog, mock_parent_window)

        # Calculate expected position
        # Parent: position=(100, 50), size=(1200, 800)
        # Dialog: size=(0, 0)
        expected_x = 100 + (1200 - 0) // 2  # 700
        expected_y = 50 + (800 - 0) // 2  # 450

        zero_dialog.position = (expected_x, expected_y)
        assert zero_dialog.position == (700, 450)

    def test_center_window_negative_parent_position(self, mock_window):
        """Test centering when parent window has negative position."""
        parent = MagicMock()
        parent.position = (-50, -25)
        parent.size = (800, 600)

        center_window_on_parent(mock_window, parent)

        # Calculate expected position
        # Parent: position=(-50, -25), size=(800, 600)
        # Dialog: size=(400, 300)
        expected_x = -50 + (800 - 400) // 2  # 150
        expected_y = -25 + (600 - 300) // 2  # 125

        mock_window.position = (expected_x, expected_y)
        assert mock_window.position == (150, 125)

    def test_center_window_integer_division(self):
        """Test that integer division is used for position calculation."""
        dialog = MagicMock()
        dialog.size = (301, 201)  # Odd numbers to test integer division

        parent = MagicMock()
        parent.position = (0, 0)
        parent.size = (1000, 600)

        center_window_on_parent(dialog, parent)

        # Calculate expected position with integer division
        # Parent: position=(0, 0), size=(1000, 600)
        # Dialog: size=(301, 201)
        expected_x = 0 + (1000 - 301) // 2  # 349
        expected_y = 0 + (600 - 201) // 2  # 199

        dialog.position = (expected_x, expected_y)
        assert dialog.position == (349, 199)

    @patch("toga.Window")
    def test_center_window_with_real_toga_import(self, mock_toga_window):
        """Test that the function can work with actual Toga window types."""
        # This test ensures the function signature is compatible with real Toga windows
        dialog = MagicMock()
        dialog.size = (400, 300)

        parent = MagicMock()
        parent.position = (100, 50)
        parent.size = (800, 600)

        # This should not raise any import or type errors
        center_window_on_parent(dialog, parent)

        expected_x = 100 + (800 - 400) // 2  # 300
        expected_y = 50 + (600 - 300) // 2  # 200

        dialog.position = (expected_x, expected_y)
        assert dialog.position == (300, 200)
