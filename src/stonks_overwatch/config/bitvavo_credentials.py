from dataclasses import dataclass

from stonks_overwatch.config.base_credentials import BaseCredentials


@dataclass
class BitvavoCredentials(BaseCredentials):
    apikey: str
    apisecret: str
