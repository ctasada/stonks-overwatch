from typing import Any, Dict

from stonks_overwatch.config.ibkr import IbkrCredentials

import pytest


class TestIbkrCredentials:
    """Test suite for IBKR credentials validation."""

    def test_valid_credentials_with_key_values(self) -> None:
        """Test that credentials are valid with direct key values."""
        creds = IbkrCredentials(
            access_token="token",
            access_token_secret="secret",
            consumer_key="key",
            dh_prime="prime",
            encryption_key="-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
            signature_key="-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
        )
        assert creds.encryption_key is not None
        assert creds.signature_key is not None
        assert creds.access_token == "token"

    def test_valid_credentials_with_file_paths(self) -> None:
        """Test that credentials are valid with file paths."""
        creds = IbkrCredentials(
            access_token="token",
            access_token_secret="secret",
            consumer_key="key",
            dh_prime="prime",
            encryption_key_fp="/path/to/encryption.pem",
            signature_key_fp="/path/to/signature.pem",
        )
        assert creds.encryption_key_fp is not None
        assert creds.signature_key_fp is not None
        assert creds.encryption_key is None
        assert creds.signature_key is None

    def test_valid_credentials_with_mixed_keys(self) -> None:
        """Test that credentials are valid with mixed key types."""
        creds = IbkrCredentials(
            access_token="token",
            access_token_secret="secret",
            consumer_key="key",
            dh_prime="prime",
            encryption_key="-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
            signature_key_fp="/path/to/signature.pem",
        )
        assert creds.encryption_key is not None
        assert creds.signature_key_fp is not None

    def test_missing_encryption_key_raises_error(self) -> None:
        """Test that missing encryption key raises ValueError."""
        with pytest.raises(ValueError, match="encryption_key"):
            IbkrCredentials(
                access_token="token",
                access_token_secret="secret",
                consumer_key="key",
                dh_prime="prime",
                signature_key="key",
            )

    def test_missing_signature_key_raises_error(self) -> None:
        """Test that missing signature key raises ValueError."""
        with pytest.raises(ValueError, match="signature_key"):
            IbkrCredentials(
                access_token="token",
                access_token_secret="secret",
                consumer_key="key",
                dh_prime="prime",
                encryption_key="key",
            )

    def test_empty_string_encryption_key_raises_error(self) -> None:
        """Test that empty string encryption key raises ValueError."""
        with pytest.raises(ValueError, match="encryption_key"):
            IbkrCredentials(
                access_token="token",
                access_token_secret="secret",
                consumer_key="key",
                dh_prime="prime",
                encryption_key="   ",
                signature_key="key",
            )

    def test_empty_string_signature_key_raises_error(self) -> None:
        """Test that empty string signature key raises ValueError."""
        with pytest.raises(ValueError, match="signature_key"):
            IbkrCredentials(
                access_token="token",
                access_token_secret="secret",
                consumer_key="key",
                dh_prime="prime",
                encryption_key="key",
                signature_key="   ",
            )

    def test_from_dict_with_valid_data(self) -> None:
        """Test from_dict with valid data."""
        data: Dict[str, Any] = {
            "access_token": "token",
            "access_token_secret": "secret",
            "consumer_key": "key",
            "dh_prime": "prime",
            "encryption_key": "enc_key",
            "signature_key": "sig_key",
        }
        creds = IbkrCredentials.from_dict(data)
        assert creds.access_token == "token"
        assert creds.access_token_secret == "secret"
        assert creds.consumer_key == "key"
        assert creds.dh_prime == "prime"
        assert creds.encryption_key == "enc_key"
        assert creds.signature_key == "sig_key"

    def test_from_dict_with_file_paths(self) -> None:
        """Test from_dict with file path data."""
        data: Dict[str, Any] = {
            "access_token": "token",
            "access_token_secret": "secret",
            "consumer_key": "key",
            "dh_prime": "prime",
            "encryption_key_fp": "/path/to/encryption.pem",
            "signature_key_fp": "/path/to/signature.pem",
        }
        creds = IbkrCredentials.from_dict(data)
        assert creds.encryption_key_fp == "/path/to/encryption.pem"
        assert creds.signature_key_fp == "/path/to/signature.pem"

    def test_from_dict_with_empty_data(self) -> None:
        """Test from_dict with empty data returns empty credentials without validation."""
        creds = IbkrCredentials.from_dict({})
        assert creds.access_token == ""
        assert creds.consumer_key == ""
        assert creds.encryption_key is None
        assert creds.signature_key is None

    def test_from_dict_filters_invalid_fields(self) -> None:
        """Test that from_dict filters out invalid fields."""
        data: Dict[str, Any] = {
            "access_token": "token",
            "access_token_secret": "secret",
            "consumer_key": "key",
            "dh_prime": "prime",
            "encryption_key": "enc_key",
            "signature_key": "sig_key",
            "invalid_field": "should_be_ignored",
            "another_invalid": 123,
        }
        creds = IbkrCredentials.from_dict(data)
        assert not hasattr(creds, "invalid_field")
        assert not hasattr(creds, "another_invalid")
        assert creds.access_token == "token"

    def test_both_encryption_key_options_provided(self) -> None:
        """Test that providing both encryption key options is valid (direct value takes precedence)."""
        creds = IbkrCredentials(
            access_token="token",
            access_token_secret="secret",
            consumer_key="key",
            dh_prime="prime",
            encryption_key="direct_key",
            encryption_key_fp="/path/to/file.pem",
            signature_key="sig_key",
        )
        assert creds.encryption_key == "direct_key"
        assert creds.encryption_key_fp == "/path/to/file.pem"

    def test_both_signature_key_options_provided(self) -> None:
        """Test that providing both signature key options is valid (direct value takes precedence)."""
        creds = IbkrCredentials(
            access_token="token",
            access_token_secret="secret",
            consumer_key="key",
            dh_prime="prime",
            encryption_key="enc_key",
            signature_key="direct_key",
            signature_key_fp="/path/to/file.pem",
        )
        assert creds.signature_key == "direct_key"
        assert creds.signature_key_fp == "/path/to/file.pem"

    def test_empty_credentials_skip_validation(self) -> None:
        """Test that completely empty credentials skip validation."""
        # This should not raise an error as all required fields are empty
        creds = IbkrCredentials("", "", "", "")
        assert creds.access_token == ""
        assert creds.access_token_secret == ""
        assert creds.consumer_key == ""
        assert creds.dh_prime == ""
