from stonks_overwatch.services.utilities.credential_validator import CredentialValidator

from unittest.mock import Mock


class TestCredentialValidator:
    def test_validate_degiro_credentials(self):
        """Test DEGIRO credential validation."""
        # Valid credentials
        valid_creds = Mock(username="myuser", password="mypassword")
        assert CredentialValidator.has_valid_credentials("degiro", valid_creds)

        # Invalid: placeholders
        placeholder_creds = Mock(username="USERNAME", password="PASSWORD")
        assert not CredentialValidator.has_valid_credentials("degiro", placeholder_creds)

        # Invalid: empty
        empty_creds = Mock(username="", password="")
        assert not CredentialValidator.has_valid_credentials("degiro", empty_creds)

        # Invalid: too short
        short_creds = Mock(username="ab", password="ab")
        assert not CredentialValidator.has_valid_credentials("degiro", short_creds)

        # Invalid: missing attributes
        missing_attr_creds = Mock()
        del missing_attr_creds.username
        assert not CredentialValidator.has_valid_credentials("degiro", missing_attr_creds)

    def test_validate_bitvavo_credentials(self):
        """Test Bitvavo credential validation."""
        # Valid credentials (length > 10)
        valid_creds = Mock(apikey="12345678901", apisecret="12345678901")
        assert CredentialValidator.has_valid_credentials("bitvavo", valid_creds)

        # Invalid: placeholders
        placeholder_creds = Mock(apikey="BITVAVO API KEY", apisecret="BITVAVO API SECRET")
        assert not CredentialValidator.has_valid_credentials("bitvavo", placeholder_creds)

        # Invalid: too short
        short_creds = Mock(apikey="short", apisecret="short")
        assert not CredentialValidator.has_valid_credentials("bitvavo", short_creds)

    def test_validate_ibkr_credentials(self):
        """Test IBKR credential validation."""
        # Valid credentials (length > 10)
        valid_creds = Mock(access_token="12345678901")
        assert CredentialValidator.has_valid_credentials("ibkr", valid_creds)

        # Invalid: placeholders
        placeholder_creds = Mock(access_token="IBKR ACCESS TOKEN")
        assert not CredentialValidator.has_valid_credentials("ibkr", placeholder_creds)

        # Invalid: too short
        short_creds = Mock(access_token="short")
        assert not CredentialValidator.has_valid_credentials("ibkr", short_creds)

    def test_unknown_broker(self):
        """Test validation for unknown broker."""
        # Any credentials should be valid for unknown broker
        creds = Mock()
        assert CredentialValidator.has_valid_credentials("unknown_broker", creds)

    def test_none_credentials(self):
        """Test validation with None credentials."""
        assert not CredentialValidator.has_valid_credentials("degiro", None)
        assert not CredentialValidator.has_valid_credentials("unknown", None)
