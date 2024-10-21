import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from settings import PROJECT_PATH


class DegiroCredentials:
    def __init__(
        self,
        username: str,
        password: str,
        int_account: Optional[int] = None,
        totp_secret_key: Optional[str] = None,
        one_time_password: Optional[int] = None,
        user_token: Optional[str] = None,
    ):
        self.username = username
        self.password = password
        self.int_account = int_account
        self.totp_secret_key = totp_secret_key
        self.user_token = user_token
        self.one_time_password = one_time_password

    def __eq__(self, value: object) -> bool:
        if isinstance(value, DegiroCredentials):
            return (
                self.username == value.username
                and self.password == value.password
                and self.int_account == value.int_account
                and self.totp_secret_key == value.totp_secret_key
                and self.user_token == value.user_token
                and self.one_time_password == value.one_time_password
            )

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "password": self.password,
            "int_account": self.int_account,
            "totp_secret_key": self.totp_secret_key,
            "user_token": self.user_token,
            "one_time_password": self.one_time_password,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DegiroCredentials":
        if not data:
            return cls("", "")
        return cls(
            username=data.get("username", ""),
            password=data.get("password", ""),
            int_account=data.get("int_account"),
            totp_secret_key=data.get("totp_secret_key"),
            user_token=data.get("user_token"),
            one_time_password=data.get("one_time_password"),
        )

    @classmethod
    def from_request(cls, request) -> "DegiroCredentials":
        session_credentials = request.session.get("credentials", {})
        return cls(
            username=session_credentials.get("username", ""),
            password=session_credentials.get("password", ""),
            int_account=session_credentials.get("int_account"),
            totp_secret_key=session_credentials.get("totp_secret_key"),
            user_token=session_credentials.get("user_token"),
            one_time_password=session_credentials.get("one_time_password"),
        )


class DegiroConfig:
    DEGIRO_CONFIG_PATH = os.path.join(PROJECT_PATH, "config", "config.json")

    def __init__(
            self,
            credentials: Optional[DegiroCredentials],
            base_currency: str,
            start_date: date,
            update_frequency_minutes: int = 5
    ) -> None:
        self.credentials = credentials
        self.base_currency = base_currency
        self.start_date = start_date
        self.update_frequency_minutes = update_frequency_minutes

    def __eq__(self, value: object) -> bool:
        if isinstance(value, DegiroConfig):
            return (
                self.credentials == value.credentials
                and self.base_currency == value.base_currency
                and self.start_date == value.start_date
            )
        return False

    @classmethod
    def from_dict(cls, data: dict) -> "DegiroConfig":
        credentials_data = data.get("credentials")
        credentials = DegiroCredentials.from_dict(credentials_data) if credentials_data else None
        base_currency = data.get("base_currency", "")
        start_date_str = data.get("start_date", "")
        # FIXME: Use Localization method
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else date.today()
        update_frequency_minutes = data.get("update_frequency_minutes", 5)

        return cls(credentials, base_currency, start_date, update_frequency_minutes)

    @classmethod
    def from_json_file(cls, file_path: str | Path) -> "DegiroConfig":
        """Loads the configuration from a JSON file."""
        data = {}
        with open(file_path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data.get("degiro", {}))

    @classmethod
    def default(cls) -> "DegiroConfig":
        return cls.from_json_file(cls.DEGIRO_CONFIG_PATH)
