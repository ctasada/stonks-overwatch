import base64
import json
import os

from cryptography.fernet import Fernet

from stonks_overwatch.settings import STONKS_OVERWATCH_DATA_DIR


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
