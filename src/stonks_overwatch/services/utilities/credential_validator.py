from typing import Any, Callable, Dict

from stonks_overwatch.constants import BrokerName
from stonks_overwatch.utils.core.logger import StonksLogger


class CredentialValidator:
    """
    Utility class for validating broker credentials.
    Centralizes validation logic to avoid duplication across middleware and views.
    """

    logger = StonksLogger.get_logger("stonks_overwatch.utils.credential_validator", "[CRED_VALIDATOR]")

    @classmethod
    def has_valid_credentials(cls, broker_name: BrokerName, credentials: Any) -> bool:
        """
        Validate that broker credentials are not placeholders and meet minimum requirements.

        Args:
            broker_name: Name of the broker (e.g., 'degiro', 'bitvavo')
            credentials: Credential object containing credentials

        Returns:
            True if credentials appear valid, False otherwise
        """
        if not credentials:
            return False

        try:
            # First check if credentials have basic fields (use existing method if available)
            if hasattr(credentials, "has_minimal_credentials"):
                if not credentials.has_minimal_credentials():
                    return False

            # Then check for placeholders using broker-specific validation
            validators: Dict[str, Callable[[Any], bool]] = {
                BrokerName.DEGIRO: cls._validate_degiro,
                BrokerName.BITVAVO: cls._validate_bitvavo,
                BrokerName.IBKR: cls._validate_ibkr,
            }

            validator = validators.get(broker_name)
            if validator:
                return validator(credentials)

            # For unknown brokers, assume valid if credentials exist
            # This allows plugin brokers to work without modifying this core class
            return True

        except Exception as e:
            cls.logger.warning(f"Error validating credentials for {broker_name}: {str(e)}")
            return False

    @staticmethod
    def _validate_degiro(credentials: Any) -> bool:
        """
        Validate DEGIRO credentials.
        Checks username and password are not placeholders and meet minimum length.
        """
        return (
            hasattr(credentials, "username")
            and hasattr(credentials, "password")
            and credentials.username
            and credentials.password
            and credentials.username != "USERNAME"
            and credentials.password != "PASSWORD"
            and len(credentials.username) > 2
            and len(credentials.password) > 2
        )

    @staticmethod
    def _validate_bitvavo(credentials: Any) -> bool:
        """
        Validate Bitvavo credentials.
        Checks API key and secret are not placeholders and meet minimum length.
        """
        return (
            hasattr(credentials, "apikey")
            and hasattr(credentials, "apisecret")
            and credentials.apikey
            and credentials.apisecret
            and credentials.apikey != "BITVAVO API KEY"
            and credentials.apisecret != "BITVAVO API SECRET"
            and len(credentials.apikey) > 10
            and len(credentials.apisecret) > 10
        )

    @staticmethod
    def _validate_ibkr(credentials: Any) -> bool:
        """
        Validate IBKR credentials.
        Checks access token is not placeholder and meets minimum length.
        """
        return (
            hasattr(credentials, "access_token")
            and credentials.access_token
            and credentials.access_token != "IBKR ACCESS TOKEN"
            and len(credentials.access_token) > 10
        )
