from stonks_overwatch.config.config import Config
from stonks_overwatch.core.models import GlobalConfiguration

import pytest
from django.test import TestCase


@pytest.mark.django_db
class TestGlobalConfiguration(TestCase):
    def test_set_and_get_setting(self):
        """Test basic set and get functionality of GlobalConfiguration model."""
        GlobalConfiguration.set_setting("test_key", "test_value")
        assert GlobalConfiguration.get_setting("test_key") == "test_value"

    def test_update_setting(self):
        """Test updating an existing setting."""
        GlobalConfiguration.set_setting("update_key", "initial")
        GlobalConfiguration.set_setting("update_key", "updated")
        assert GlobalConfiguration.get_setting("update_key") == "updated"

    def test_get_non_existent_setting(self):
        """Test getting a non-existent setting returns default."""
        assert GlobalConfiguration.get_setting("no_key", "default_val") == "default_val"


@pytest.mark.django_db
class TestConfigDBIntegration(TestCase):
    def setUp(self):
        # Reset global instance for testing
        Config.reset_global_for_tests()
        self.config = Config.get_global()

    def test_config_base_currency_persistence(self):
        """Test that base_currency is persisted to DB via Config class."""
        self.config.base_currency = "USD"

        # Verify it's in DB
        assert GlobalConfiguration.get_setting("base_currency") == "USD"

        # Reset and reload to verify persistence
        Config.reset_global_for_tests()
        new_config = Config.get_global()
        assert new_config.base_currency == "USD"

    def test_config_appearance_persistence(self):
        """Test that appearance setting is persisted."""
        self.config.appearance = "dark"

        # Verify it's in DB
        assert GlobalConfiguration.get_setting("appearance") == "dark"

        # Reset and reload
        Config.reset_global_for_tests()
        new_config = Config.get_global()
        assert new_config.appearance == "dark"

    def test_appearance_validation(self):
        """Test that invalid appearance values raise ValueError."""
        with pytest.raises(ValueError):
            self.config.appearance = "invalid_style"

    def test_json_override_precedence(self):
        """
        Test that values passed to Config (usually from JSON) take precedence
        over DB values for base_currency.
        """
        # Set a value in DB
        GlobalConfiguration.set_setting("base_currency", "GBP")

        # Create a config instance with a different currency (simulating JSON load)
        config_with_override = Config(base_currency="JPY")

        assert config_with_override.base_currency == "JPY"
