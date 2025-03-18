from dataclasses import dataclass
from typing import Any, Dict, Optional

from stonks_overwatch.config.base_credentials import BaseCredentials

@dataclass
class DegiroCredentials(BaseCredentials):
    username: str
    password: str
    int_account: Optional[int] = None
    totp_secret_key: Optional[str] = None
    one_time_password: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DegiroCredentials":
        if not data:
            return cls("", "")
        return cls(**data)

    @classmethod
    def from_request(cls, request) -> "DegiroCredentials":
        session_credentials = request.session.get("credentials", {})
        return cls.from_dict(session_credentials)
