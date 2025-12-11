"""Tests for settings module."""

import pytest
from unittest.mock import patch


@pytest.mark.django_db
class TestEnsureDataDirectories:
    """Test cases for ensure_data_directories function."""

    def test_ensure_data_directories_creates_missing_directories(self, tmp_path):
        """Test that ensure_data_directories creates missing directories."""
        # Set up test directories
        test_data_dir = tmp_path / "data"
        test_cache_dir = tmp_path / "cache"
        test_logs_dir = tmp_path / "logs"

        # Verify directories don't exist yet
        assert not test_data_dir.exists()
        assert not test_cache_dir.exists()
        assert not test_logs_dir.exists()

        with patch.dict(
            "os.environ",
            {
                "STONKS_OVERWATCH_DATA_DIR": str(test_data_dir),
                "STONKS_OVERWATCH_CACHE_DIR": str(test_cache_dir),
                "STONKS_OVERWATCH_LOGS_DIR": str(test_logs_dir),
            },
        ):
            # Re-import settings to pick up new env vars
            import importlib

            import stonks_overwatch.settings as settings_module

            importlib.reload(settings_module)

            # Call the function
            settings_module.ensure_data_directories()

            # Verify directories were created
            assert test_data_dir.exists()
            assert test_cache_dir.exists()
            assert test_logs_dir.exists()

    def test_ensure_data_directories_handles_existing_directories(self, tmp_path):
        """Test that ensure_data_directories handles existing directories gracefully."""
        # Set up test directories that already exist
        test_data_dir = tmp_path / "data"
        test_cache_dir = tmp_path / "cache"
        test_logs_dir = tmp_path / "logs"

        # Create directories
        test_data_dir.mkdir()
        test_cache_dir.mkdir()
        test_logs_dir.mkdir()

        # Create a test file to verify directories aren't wiped
        test_file = test_data_dir / "test.txt"
        test_file.write_text("test content")

        with patch.dict(
            "os.environ",
            {
                "STONKS_OVERWATCH_DATA_DIR": str(test_data_dir),
                "STONKS_OVERWATCH_CACHE_DIR": str(test_cache_dir),
                "STONKS_OVERWATCH_LOGS_DIR": str(test_logs_dir),
            },
        ):
            # Re-import settings to pick up new env vars
            import importlib

            import stonks_overwatch.settings as settings_module

            importlib.reload(settings_module)

            # Call the function - should not raise error
            settings_module.ensure_data_directories()

            # Verify directories still exist
            assert test_data_dir.exists()
            assert test_cache_dir.exists()
            assert test_logs_dir.exists()

            # Verify existing file is still there
            assert test_file.exists()
            assert test_file.read_text() == "test content"

    def test_ensure_data_directories_creates_nested_directories(self, tmp_path):
        """Test that ensure_data_directories creates nested directories."""
        # Set up test directory with nested path
        test_data_dir = tmp_path / "level1" / "level2" / "data"
        test_cache_dir = tmp_path / "level1" / "level2" / "cache"
        test_logs_dir = tmp_path / "level1" / "level2" / "logs"

        # Verify parent directories don't exist
        assert not (tmp_path / "level1").exists()

        with patch.dict(
            "os.environ",
            {
                "STONKS_OVERWATCH_DATA_DIR": str(test_data_dir),
                "STONKS_OVERWATCH_CACHE_DIR": str(test_cache_dir),
                "STONKS_OVERWATCH_LOGS_DIR": str(test_logs_dir),
            },
        ):
            # Re-import settings to pick up new env vars
            import importlib

            import stonks_overwatch.settings as settings_module

            importlib.reload(settings_module)

            # Call the function
            settings_module.ensure_data_directories()

            # Verify nested directories were created
            assert test_data_dir.exists()
            assert test_cache_dir.exists()
            assert test_logs_dir.exists()
