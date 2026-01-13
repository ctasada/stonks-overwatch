class SessionKeys:
    """
    Central repository for session keys used across the application.
    Prevents hardcoded strings and typos.
    """

    # Generic templates
    _BROKER_AUTHENTICATED = "{}_authenticated"
    _BROKER_TOTP_REQUIRED = "{}_totp_required"
    _BROKER_IN_APP_AUTH_REQUIRED = "{}_in_app_auth_required"
    _BROKER_CREDENTIALS = "{}_credentials"

    # Legacy/Specific keys
    DEGIRO_CREDENTIALS = "degiro_credentials"

    @classmethod
    def get_authenticated_key(cls, broker_name: str) -> str:
        """Get the session key for checking if a broker is authenticated."""
        return cls._BROKER_AUTHENTICATED.format(broker_name)

    @classmethod
    def get_totp_required_key(cls, broker_name: str) -> str:
        """Get the session key for checking if TOTP is required for a broker."""
        return cls._BROKER_TOTP_REQUIRED.format(broker_name)

    @classmethod
    def get_in_app_auth_required_key(cls, broker_name: str) -> str:
        """Get the session key for checking if in-app authentication is required."""
        return cls._BROKER_IN_APP_AUTH_REQUIRED.format(broker_name)

    @classmethod
    def get_credentials_key(cls, broker_name: str) -> str:
        """Get the session key for storing broker credentials (enc/references)."""
        if broker_name == "degiro":
            return cls.DEGIRO_CREDENTIALS
        return cls._BROKER_CREDENTIALS.format(broker_name)
