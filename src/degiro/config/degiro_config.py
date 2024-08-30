import json
import os
from datetime import date, datetime
from typing import Self

from stocks_portfolio.settings import PROJECT_PATH


class DegiroCredentials:
    def __init__(self, username, password, int_account, totp_secret_key, user_token):
        self.username = username
        self.password = password
        self.int_account = int_account
        self.totp_secret_key = totp_secret_key
        self.user_token = user_token


class DegiroConfig:
    DEGIRO_CONFIG_PATH = os.path.join(PROJECT_PATH, "config", "config.json")

    def __init__(self, credentials: DegiroCredentials, base_currency: str, start_date: date):
        self.credentials = credentials
        self.start_date = start_date
        self.base_currency = base_currency

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        credentials_data = data.get("credentials", {})
        credentials = DegiroCredentials(
            username=credentials_data["username"],
            password=credentials_data["password"],
            int_account=credentials_data["int_account"],
            totp_secret_key=credentials_data["totp_secret_key"],
            user_token=credentials_data["user_token"],
        )
        base_currency = data.get("base_currency", "")
        start_date = data.get("start_date", "")
        # FIXME: Use Localization method
        return cls(credentials, base_currency, datetime.strptime(start_date, "%Y-%m-%d"))

    @classmethod
    def from_json_file(cls, file_path) -> Self:
        with open(file_path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data.get("degiro", {}))

    @classmethod
    def default(cls) -> Self:
        return cls.from_json_file(cls.DEGIRO_CONFIG_PATH)
