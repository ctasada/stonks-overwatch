from typing import Any, Callable, Dict

from stonks_overwatch.utils.core.logger import StonksLogger


class CredentialValidator:
    """
    Utility class for validating broker credentials.
    Centralizes validation logic to avoid duplication across middleware and views.
    """

    logger = StonksLogger.get_logger("stonks_overwatch.utils.credential_validator", "[CRED_VALIDATOR]")

    @classmethod
    def has_valid_credentials(cls, broker_name: str, credentials: Any) -> bool:
        """
        Validate that broker credentials are not placeholders and meet minimum requirements.

        Args:
            broker_name: Name of the broker (e.g., 'degiro', 'bitvavo')
            credentials: Credential object or dictionary containing credentials

        Returns:
            True if credentials appear valid, False otherwise
        """
        if not credentials:
            return False

        try:
            validators: Dict[str, Callable[[Any], bool]] = {
                "degiro": cls._validate_degiro,
                "bitvavo": cls._validate_bitvavo,
                "ibkr": cls._validate_ibkr,
            }

            validator = validators.get(broker_name)
            if validator:
                return validator(credentials)

            # For unknown brokers, assume valid if credentials exist
            # This allows plugin brokers to work without modifying this core class
            # Ideally plugins would register their own validators
            return True

        except Exception as e:
            cls.logger.warning(f"Error validating credentials for {broker_name}: {str(e)}")
            return False

    @staticmethod
    def _validate_degiro(credentials: Any) -> bool:
        """
        Validate DEGIRO credentials.
        Checks username and password validation.
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
        Checks API key and secret.
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
        Checks access token.
        """
        return (
            hasattr(credentials, "access_token")
            and credentials.access_token
            and credentials.access_token != "IBKR ACCESS TOKEN"
            and len(credentials.access_token) > 10
        )
