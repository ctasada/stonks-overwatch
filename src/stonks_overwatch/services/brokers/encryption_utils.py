import base64
import json
import os

from cryptography.fernet import Fernet

from stonks_overwatch.settings import STONKS_OVERWATCH_DATA_DIR
from stonks_overwatch.utils.core.logger import StonksLogger

logger = StonksLogger.get_logger("stonks_overwatch.brokers.encryption", "[ENCRYPTION]")


def get_fernet():
    key_file = os.path.join(STONKS_OVERWATCH_DATA_DIR, "fernet.key")
    # If the key file does not exist, create it
    if not os.path.exists(key_file):
        key = Fernet.generate_key()
        with open(key_file, "wb") as f:
            f.write(key)
    else:
        with open(key_file, "rb") as f:
            key = f.read()
    return Fernet(key)


def encrypt_dict(data: dict) -> str:
    f = get_fernet()
    json_data = json.dumps(data)
    token = f.encrypt(json_data.encode())
    return base64.urlsafe_b64encode(token).decode()


def decrypt_dict(token: str) -> dict:
    f = get_fernet()
    decrypted = f.decrypt(base64.urlsafe_b64decode(token.encode()))
    return json.loads(decrypted.decode())


def encrypt_integration_config(config: dict) -> dict:
    """Encrypt the ``api_key`` field in an integration config dict.

    Removes the plaintext ``api_key`` and stores it as ``api_key_enc``
    (a Fernet-encrypted, base64-encoded blob).  If ``api_key`` is absent
    or empty the config is returned unchanged (without any key fields).

    Args:
        config: Dict with at least ``enabled`` and optionally ``api_key``.

    Returns:
        A new dict with ``api_key`` replaced by ``api_key_enc``.
    """
    if not isinstance(config, dict):
        return {}

    api_key = config.get("api_key", "").strip()
    result = {k: v for k, v in config.items() if k not in ("api_key", "api_key_enc")}

    if api_key:
        result["api_key_enc"] = encrypt_dict({"api_key": api_key})

    return result


def decrypt_integration_config(config: dict) -> dict:
    """Decrypt the ``api_key_enc`` field in an integration config dict back to ``api_key``.

    If decryption fails (e.g. missing or rotated fernet key) the returned
    dict will contain neither ``api_key`` nor ``api_key_enc``, effectively
    disabling the integration rather than leaking a corrupt value.

    Args:
        config: Dict that may contain ``api_key_enc``.

    Returns:
        A new dict with ``api_key_enc`` replaced by the plaintext ``api_key``.
    """
    if not isinstance(config, dict):
        return {}

    api_key_enc = config.get("api_key_enc")
    if not api_key_enc:
        return config

    result = {k: v for k, v in config.items() if k != "api_key_enc"}
    try:
        decrypted = decrypt_dict(api_key_enc)
        api_key = decrypted.get("api_key", "")
        if api_key:
            result["api_key"] = api_key
    except Exception as e:
        # Decryption failure (e.g. rotated fernet key) — omit the key entirely
        # so the integration is disabled rather than crashing or leaking bad data.
        logger.warning("Failed to decrypt integration API key; integration will be disabled. (%s)", type(e).__name__)

    return result
