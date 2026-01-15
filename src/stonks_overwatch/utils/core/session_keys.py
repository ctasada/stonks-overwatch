from stonks_overwatch.constants.brokers import BrokerName


class SessionKeys:
    """
    Central repository for session keys used across the application.
    Prevents hardcoded strings and typos.

    Methods accept both BrokerName enum and string values for flexibility.
    Using BrokerName enum is recommended for type safety.
    """

    # Generic templates
    _BROKER_AUTHENTICATED = "{}_authenticated"
    _BROKER_TOTP_REQUIRED = "{}_totp_required"
    _BROKER_IN_APP_AUTH_REQUIRED = "{}_in_app_auth_required"
    _BROKER_CREDENTIALS = "{}_credentials"

    @classmethod
    def get_authenticated_key(cls, broker_name: BrokerName) -> str:
        """Get the session key for checking if a broker is authenticated.

        Args:
            broker_name: Broker name

        Returns:
            Session key string

        Example:
            >>> SessionKeys.get_authenticated_key(BrokerName.DEGIRO)
            'degiro_authenticated'
        """
        return cls._BROKER_AUTHENTICATED.format(broker_name)

    @classmethod
    def get_totp_required_key(cls, broker_name: BrokerName) -> str:
        """Get the session key for checking if TOTP is required for a broker.

        Args:
            broker_name: Broker name

        Returns:
            Session key string
        """
        return cls._BROKER_TOTP_REQUIRED.format(broker_name)

    @classmethod
    def get_in_app_auth_required_key(cls, broker_name: BrokerName) -> str:
        """Get the session key for checking if in-app authentication is required.

        Args:
            broker_name: Broker name

        Returns:
            Session key string
        """
        return cls._BROKER_IN_APP_AUTH_REQUIRED.format(broker_name)

    @classmethod
    def get_credentials_key(cls, broker_name: BrokerName) -> str:
        """Get the session key for storing broker credentials (enc/references).

        Args:
            broker_name: Broker name

        Returns:
            Session key string
        """
        return cls._BROKER_CREDENTIALS.format(broker_name)
