"""
Unit tests for SessionKeys utility.
"""

from stonks_overwatch.utils.core.session_keys import SessionKeys

from django.test import TestCase


class TestSessionKeys(TestCase):
    """Test cases for SessionKeys utility class."""

    def test_get_authenticated_key(self):
        """Test generating authenticated session keys."""
        assert SessionKeys.get_authenticated_key("degiro") == "degiro_authenticated"
        assert SessionKeys.get_authenticated_key("bitvavo") == "bitvavo_authenticated"
        assert SessionKeys.get_authenticated_key("ibkr") == "ibkr_authenticated"
        assert SessionKeys.get_authenticated_key("test_broker") == "test_broker_authenticated"

    def test_get_totp_required_key(self):
        """Test generating TOTP required session keys."""
        assert SessionKeys.get_totp_required_key("degiro") == "degiro_totp_required"
        assert SessionKeys.get_totp_required_key("bitvavo") == "bitvavo_totp_required"
        assert SessionKeys.get_totp_required_key("test_broker") == "test_broker_totp_required"

    def test_get_in_app_auth_required_key(self):
        """Test generating in-app auth required session keys."""
        assert SessionKeys.get_in_app_auth_required_key("degiro") == "degiro_in_app_auth_required"
        assert SessionKeys.get_in_app_auth_required_key("bitvavo") == "bitvavo_in_app_auth_required"
        assert SessionKeys.get_in_app_auth_required_key("test_broker") == "test_broker_in_app_auth_required"

    def test_get_credentials_key(self):
        """Test generating credentials session keys."""
        # Special case for degiro
        assert SessionKeys.get_credentials_key("degiro") == "degiro_credentials"

        # Standard format for others
        assert SessionKeys.get_credentials_key("bitvavo") == "bitvavo_credentials"
        assert SessionKeys.get_credentials_key("ibkr") == "ibkr_credentials"
        assert SessionKeys.get_credentials_key("test_broker") == "test_broker_credentials"
