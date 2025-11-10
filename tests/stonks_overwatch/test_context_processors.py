from stonks_overwatch.context_processors import app_mode_processor

from unittest.mock import Mock


class TestAppModeProcessor:
    """Test cases for app_mode_processor context processor"""

    def test_is_desktop_app_when_env_var_set(self, monkeypatch):
        """Test that is_desktop_app is True when STONKS_OVERWATCH_APP env var is set to '1'"""
        monkeypatch.setenv("STONKS_OVERWATCH_APP", "1")
        request = Mock()

        result = app_mode_processor(request)

        assert result["is_desktop_app"] is True
        assert result["is_webapp"] is False

    def test_is_webapp_when_env_var_not_set(self, monkeypatch):
        """Test that is_webapp is True when STONKS_OVERWATCH_APP env var is not set"""
        monkeypatch.delenv("STONKS_OVERWATCH_APP", raising=False)
        request = Mock()

        result = app_mode_processor(request)

        assert result["is_desktop_app"] is False
        assert result["is_webapp"] is True

    def test_is_webapp_when_env_var_set_to_other_value(self, monkeypatch):
        """Test that is_webapp is True when STONKS_OVERWATCH_APP env var is set to a value other than '1'"""
        monkeypatch.setenv("STONKS_OVERWATCH_APP", "0")
        request = Mock()

        result = app_mode_processor(request)

        assert result["is_desktop_app"] is False
        assert result["is_webapp"] is True

    def test_is_webapp_when_env_var_is_empty_string(self, monkeypatch):
        """Test that is_webapp is True when STONKS_OVERWATCH_APP env var is empty string"""
        monkeypatch.setenv("STONKS_OVERWATCH_APP", "")
        request = Mock()

        result = app_mode_processor(request)

        assert result["is_desktop_app"] is False
        assert result["is_webapp"] is True
