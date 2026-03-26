import shutil
import tempfile

from stonks_overwatch.services.brokers import encryption_utils

import pytest


@pytest.fixture
def temp_data_dir(monkeypatch):
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setattr(encryption_utils, "STONKS_OVERWATCH_DATA_DIR", temp_dir)
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def fernet_key(temp_data_dir):
    """Ensure a Fernet key exists before tests that need encryption."""
    encryption_utils.get_fernet()
    return temp_data_dir


class TestBrokersConfigurationInit:
    def test_init_with_encrypted_string_decrypts_credentials(self, fernet_key):
        """Credentials stored as an encrypted string are decrypted on init."""
        from stonks_overwatch.services.brokers.models import BrokersConfiguration

        raw = {"username": "alice", "password": "secret"}
        encrypted = encryption_utils.encrypt_dict(raw)

        instance = BrokersConfiguration(broker_name="degiro", enabled=True, credentials=encrypted)

        assert instance.credentials == raw

    def test_init_with_dict_credentials_skips_decryption(self, fernet_key):
        """Credentials already a dict (e.g. redacted dump) are left unchanged without error."""
        from stonks_overwatch.services.brokers.models import BrokersConfiguration

        redacted = {"username": True, "password": False}

        instance = BrokersConfiguration(broker_name="degiro", enabled=True, credentials=redacted)

        assert instance.credentials == redacted

    def test_init_with_none_credentials_does_not_raise(self, fernet_key):
        """None credentials do not trigger decryption."""
        from stonks_overwatch.services.brokers.models import BrokersConfiguration

        instance = BrokersConfiguration(broker_name="degiro", enabled=True, credentials=None)

        assert instance.credentials is None

    def test_init_with_empty_dict_credentials_does_not_raise(self, fernet_key):
        """Empty dict credentials do not trigger decryption."""
        from stonks_overwatch.services.brokers.models import BrokersConfiguration

        instance = BrokersConfiguration(broker_name="degiro", enabled=True, credentials={})

        assert instance.credentials == {}
