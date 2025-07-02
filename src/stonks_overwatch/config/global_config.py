"""
Global configuration singleton for cached configuration access.

This module provides a singleton class that loads the configuration once
and caches it for subsequent access, reducing redundant configuration creation.
"""

from stonks_overwatch.config.config import Config
from stonks_overwatch.config.config_factory import config_factory
from stonks_overwatch.utils.core.singleton import singleton


@singleton
class GlobalConfig:
    """
    Global configuration singleton that loads once and caches the result.

    This class provides a centralized way to access the application configuration
    without creating new instances on every access.
    """

    def __init__(self):
        self._config = None
        self._factory = config_factory

    def get_config(self) -> Config:
        """
        Get the global configuration instance, creating it if necessary.

        Returns:
            The global configuration instance
        """
        if self._config is None:
            self._config = Config._default()
        return self._config

    def refresh_config(self) -> Config:
        """
        Force refresh of the global configuration.

        This is useful when configuration files have been updated
        or when runtime configuration changes are needed.

        Returns:
            The refreshed configuration instance
        """
        self._config = Config._default()
        return self._config

    def clear_cache(self, broker_name: str = None) -> None:
        """
        Clear the configuration cache.

        Args:
            broker_name: Optional broker name. If provided, only clears cache for that broker.
                        If None, clears all cached configurations.
        """
        self._factory.clear_cache(broker_name)
        # Also clear the global config instance to force refresh
        self._config = None

    def refresh_broker_config(self, broker_name: str) -> None:
        """
        Refresh configuration for a specific broker.

        Args:
            broker_name: Name of the broker to refresh
        """
        self._factory.refresh_default_config(broker_name)
        # Clear the global config instance to force refresh
        self._config = None

    def update_degiro_credentials(
        self,
        username: str,
        password: str,
        int_account: int = None,
        totp_secret_key: str = None,
        one_time_password: int = None,
    ) -> None:
        """
        Update DeGiro credentials in the global configuration.

        This method provides a centralized way to update DeGiro credentials
        in the global configuration, following the Single Responsibility Principle.

        Args:
            username: The username
            password: The password
            int_account: Optional internal account number
            totp_secret_key: Optional TOTP secret key
            one_time_password: Optional one-time password
        """
        try:
            config = self.get_config()
            degiro_config = config.registry.get_broker_config("degiro")

            if degiro_config is not None:
                from stonks_overwatch.config.degiro import DegiroCredentials

                degiro_credentials = DegiroCredentials(
                    username=username,
                    password=password,
                    int_account=int_account,
                    totp_secret_key=totp_secret_key,
                    one_time_password=one_time_password,
                )

                degiro_config.credentials = degiro_credentials
                # Use the logger from the config module
                from stonks_overwatch.utils.core.logger import StonksLogger

                logger = StonksLogger.get_logger("stonks_overwatch.config", "[GLOBAL_CONFIG]")
                logger.info("DeGiro credentials updated successfully in global configuration")
            else:
                from stonks_overwatch.utils.core.logger import StonksLogger

                logger = StonksLogger.get_logger("stonks_overwatch.config", "[GLOBAL_CONFIG]")
                logger.warning("DeGiro configuration not found in global config")
        except Exception as e:
            from stonks_overwatch.utils.core.logger import StonksLogger

            logger = StonksLogger.get_logger("stonks_overwatch.config", "[GLOBAL_CONFIG]")
            logger.error(f"Failed to update DeGiro credentials in global configuration: {e}")


# Global instance
global_config = GlobalConfig()
