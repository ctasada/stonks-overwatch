import base64
import os
import shutil
import tempfile

from cryptography.fernet import InvalidToken

from stonks_overwatch.services.brokers import encryption_utils

import pytest


@pytest.fixture
def temp_data_dir(monkeypatch):
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setattr(encryption_utils, "STONKS_OVERWATCH_DATA_DIR", temp_dir)
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_encrypt_decrypt_dict(temp_data_dir):
    key_path = os.path.join(temp_data_dir, "fernet.key")
    if os.path.exists(key_path):
        os.remove(key_path)
    data = {"username": "testuser", "password": "secret"}
    encrypted = encryption_utils.encrypt_dict(data)
    assert isinstance(encrypted, str)
    decrypted = encryption_utils.decrypt_dict(encrypted)
    assert decrypted == data


def test_encrypt_dict_returns_str(temp_data_dir):
    data = {"foo": "bar"}
    encrypted = encryption_utils.encrypt_dict(data)
    assert isinstance(encrypted, str)


def test_decrypt_dict_invalid_token(temp_data_dir):
    invalid_token = base64.urlsafe_b64encode(b"invalid_token").decode()
    with pytest.raises(InvalidToken):
        encryption_utils.decrypt_dict(invalid_token)


def test_key_file_created_and_reused(temp_data_dir):
    key_path = os.path.join(temp_data_dir, "fernet.key")
    if os.path.exists(key_path):
        os.remove(key_path)
    data = {"a": 1}
    encryption_utils.encrypt_dict(data)
    assert os.path.exists(key_path)
    with open(key_path, "rb") as f:
        key_content = f.read()
    encryption_utils.encrypt_dict(data)
    with open(key_path, "rb") as f:
        assert f.read() == key_content


def test_decrypt_with_missing_key(temp_data_dir):
    key_path = os.path.join(temp_data_dir, "fernet.key")
    data = {"secret": "value"}
    encrypted = encryption_utils.encrypt_dict(data)
    if os.path.exists(key_path):
        os.remove(key_path)
    with pytest.raises(InvalidToken):
        encryption_utils.decrypt_dict(encrypted)
