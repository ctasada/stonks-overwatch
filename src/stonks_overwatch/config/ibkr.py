from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.base_credentials import BaseCredentials
from stonks_overwatch.constants import BrokerName
from stonks_overwatch.utils.core.localization import LocalizationUtility


@dataclass
class IbkrCredentials(BaseCredentials):
    access_token: str
    access_token_secret: str
    consumer_key: str
    dh_prime: str
    encryption_key_fp: Optional[str] = None
    encryption_key: Optional[str] = None
    signature_key_fp: Optional[str] = None
    signature_key: Optional[str] = None

    def __post_init__(self) -> None:
        """
        Validate IBKR credentials after initialization.

        Ensures that at least one encryption key option (file path or direct content)
        and one signature key option are provided when credentials are not empty.

        Raises:
            ValueError: If encryption key is missing (neither encryption_key_fp nor encryption_key provided)
            ValueError: If signature key is missing (neither signature_key_fp nor signature_key provided)

        Note:
            Validation is skipped if all required OAuth fields are empty, allowing for
            empty credential objects during initialization.
        """
        # Skip validation if this is an empty credentials object (all required fields are empty)
        # This handles the defensive case in from_dict when data is empty
        if not (self.access_token or self.access_token_secret or self.consumer_key or self.dh_prime):
            return

        # Validate encryption key
        self._validate_key_option(
            key_value=self.encryption_key,
            key_fp=self.encryption_key_fp,
            key_name="encryption_key",
            key_display_name="Encryption Key",
        )

        # Validate signature key
        self._validate_key_option(
            key_value=self.signature_key,
            key_fp=self.signature_key_fp,
            key_name="signature_key",
            key_display_name="Signature Key",
        )

    def _validate_key_option(
        self, key_value: Optional[str], key_fp: Optional[str], key_name: str, key_display_name: str
    ) -> None:
        """
        Validate that at least one key option (file path or direct value) is provided.

        Args:
            key_value: Direct key value (PEM content)
            key_fp: File path to key file
            key_name: Technical name of the key field (e.g., 'encryption_key')
            key_display_name: User-friendly display name (e.g., 'Encryption Key')

        Raises:
            ValueError: If neither key option is provided or both are empty/whitespace
        """
        has_key = bool(key_fp and key_fp.strip()) or bool(key_value and key_value.strip())
        if not has_key:
            raise ValueError(
                f"IBKR {key_display_name} is required. Please provide either:\n"
                f"  • '{key_name}_fp': Path to your PEM file, OR\n"
                f"  • '{key_name}': Direct PEM content"
            )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IbkrCredentials":
        if not data:
            return cls("", "", "", "")
        # Extract only the fields that exist in the dataclass
        valid_fields = {
            "access_token",
            "access_token_secret",
            "consumer_key",
            "dh_prime",
            "encryption_key_fp",
            "encryption_key",
            "signature_key_fp",
            "signature_key",
        }
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


class IbkrConfig(BaseConfig):
    config_key = BrokerName.IBKR.value
    # As per https://www.interactivebrokers.com/campus/ibkr-api-page/cpapi-v1/#pacing-limitations
    # Some endpoints have a limit of 15 requests per minute: ie: /pa/transactions
    DEFAULT_IBKR_UPDATE_FREQUENCY = 15
    DEFAULT_IBKR_START_DATE_STR = "2020-01-01"
    DEFAULT_IBKR_START_DATE = LocalizationUtility.convert_string_to_date(DEFAULT_IBKR_START_DATE_STR)

    def __init__(
        self,
        credentials: Optional[IbkrCredentials],
        start_date: date,
        update_frequency_minutes: int = DEFAULT_IBKR_UPDATE_FREQUENCY,
        enabled: bool = False,
        offline_mode: bool = None,
    ) -> None:
        if offline_mode is None:
            from stonks_overwatch.utils.core.demo_mode import is_demo_mode

            offline_mode = is_demo_mode()

        self.logger.info(f"Initializing IbkrConfig with offline_mode={offline_mode}")
        super().__init__(credentials, start_date, enabled, offline_mode, update_frequency_minutes)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, IbkrConfig):
            return super().__eq__(value)
        return False

    def __repr__(self) -> str:
        return (
            f"IbkrConfig(enabled={self.enabled}, "
            f"offline_mode={self.offline_mode}, "
            f"credentials={self.credentials}, "
            f"start_date={self.start_date}, "
            f"update_frequency_minutes={self.update_frequency_minutes})"
        )

    @property
    def get_credentials(self) -> IbkrCredentials:
        return self.credentials

    @classmethod
    def from_dict(cls, data: dict) -> "IbkrConfig":
        enabled = data.get("enabled", False)
        credentials_data = data.get("credentials")
        credentials = IbkrCredentials.from_dict(credentials_data) if credentials_data else None
        start_date = data.get("start_date", cls.DEFAULT_IBKR_START_DATE)
        if isinstance(start_date, str):
            start_date = LocalizationUtility.convert_string_to_date(start_date)
        update_frequency_minutes = data.get("update_frequency_minutes", cls.DEFAULT_IBKR_UPDATE_FREQUENCY)

        from stonks_overwatch.utils.core.demo_mode import is_demo_mode

        demo_mode = is_demo_mode()
        if demo_mode:
            offline_mode = True
        else:
            # Only use offline_mode from data if explicitly set, otherwise let constructor check DEMO_MODE
            offline_mode = data.get("offline_mode") if "offline_mode" in data else None

        return cls(credentials, start_date, update_frequency_minutes, enabled, offline_mode)

    @classmethod
    def default(cls) -> "IbkrConfig":
        try:
            return cls.from_db_with_json_override(BrokerName.IBKR)
        except Exception:
            cls.logger.debug("Cannot find IBKR configuration file. Using default values")
            return IbkrConfig(
                credentials=None,
                start_date=cls.DEFAULT_IBKR_START_DATE,
                update_frequency_minutes=cls.DEFAULT_IBKR_UPDATE_FREQUENCY,
            )
