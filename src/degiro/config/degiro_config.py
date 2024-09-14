import json
import os
from datetime import date, datetime
from typing import Optional

from stocks_portfolio.settings import PROJECT_PATH


class DegiroCredentials:
    def __init__(self,
                 username: str,
                 password: str,
                 int_account: Optional[str] = None,
                 totp_secret_key: Optional[str] = None,
                 one_time_password: Optional[str] = None,
                 user_token: Optional[str] = None):
        self.username = username
        self.password = password
        self.int_account = int_account
        self.totp_secret_key = totp_secret_key
        self.user_token = user_token
        self.one_time_password = one_time_password

    def to_dict(self) -> dict:
        return {
            'username': self.username,
            'password': self.password,
            'int_account': self.int_account,
            'totp_secret_key': self.totp_secret_key,
            'user_token': self.user_token,
            'one_time_password': self.one_time_password,
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
            one_time_password=data.get("one_time_password")
        )

    @classmethod
    def from_request(cls, request) -> "DegiroCredentials":
        session_credentials = request.session.get('credentials', {})
        return cls(
            username=session_credentials.get('username', ""),
            password=session_credentials.get('password', ""),
            int_account=session_credentials.get('int_account'),
            totp_secret_key=session_credentials.get('totp_secret_key'),
            user_token=session_credentials.get('user_token'),
            one_time_password=session_credentials.get('one_time_password')
        )


class DegiroConfig:
    DEGIRO_CONFIG_PATH = os.path.join(PROJECT_PATH, "config", "config.json")

    def __init__(self,
                 credentials: Optional[DegiroCredentials],
                 base_currency: str,
                 start_date: date):
        self.credentials = credentials
        self.base_currency = base_currency
        self.start_date = start_date

    @classmethod
    def from_dict(cls, data: dict) -> "DegiroConfig":
        credentials_data = data.get("credentials")
        credentials = DegiroCredentials.from_dict(credentials_data) if credentials_data else None
        base_currency = data.get("base_currency", "")
        start_date_str = data.get("start_date", "")
        # FIXME: Use Localization method
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else date.today()
        return cls(credentials, base_currency, start_date)

    @classmethod
    def from_json_file(cls, file_path: str) -> "DegiroConfig":
        """Loads the configuration from a JSON file."""
        data = {}
        with open(file_path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data.get("degiro", {}))

    @classmethod
    def default(cls) -> "DegiroConfig":
        return cls.from_json_file(cls.DEGIRO_CONFIG_PATH)
