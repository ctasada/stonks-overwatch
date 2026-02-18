"""
Authentication helper utilities.

This module provides centralized authentication helper functions to unify
"is broker ready" logic across middleware and views.
"""

from typing import Optional

from django.http import HttpRequest

from stonks_overwatch.constants import BrokerName
from stonks_overwatch.core.factories.broker_factory import BrokerFactory
from stonks_overwatch.core.factories.broker_registry import BrokerRegistry
from stonks_overwatch.services.utilities.credential_validator import CredentialValidator
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.core.session_keys import SessionKeys


class AuthenticationHelper:
    """
    Centralized helper for authentication-related operations.

    This class provides unified logic for checking if brokers are ready,
    avoiding duplication between middleware and views.
    """

    logger = StonksLogger.get_logger("stonks_overwatch.core.authentication_helper", "[AUTH_HELPER]")

    @classmethod
    def is_broker_ready(cls, broker_name: BrokerName, request: Optional[HttpRequest] = None) -> bool:
        """
        Check if a broker is ready for use (enabled and has valid credentials).

        This method provides unified logic for determining if a broker can be used,
        combining configuration checks and credential validation.

        Args:
            broker_name: Name of the broker to check
            request: Optional HTTP request for session-based checks

        Returns:
            bool: True if broker is ready, False otherwise
        """
        try:
            # Check if broker is registered
            registry = BrokerRegistry()
            if broker_name not in registry.get_registered_brokers():
                cls.logger.debug(f"Broker {broker_name} is not registered")
                return False

            # Get broker configuration
            factory = BrokerFactory()
            config = factory.create_config(broker_name)

            if not config:
                cls.logger.debug(f"No configuration found for broker {broker_name}")
                return False

            # Check if broker is enabled
            if not config.is_enabled():
                cls.logger.debug(f"Broker {broker_name} is disabled in configuration")
                return False

            # Check if broker has valid credentials
            credentials = config.get_credentials
            if not credentials or not CredentialValidator.has_valid_credentials(broker_name, credentials):
                cls.logger.debug(f"Broker {broker_name} has invalid or missing credentials")
                return False

            cls.logger.debug(f"Broker {broker_name} is ready")
            return True

        except Exception as e:
            cls.logger.warning(f"Error checking if broker {broker_name} is ready: {str(e)}")
            return False

    @classmethod
    def get_first_ready_broker(cls) -> Optional[BrokerName]:
        """
        Get the first broker that is ready for use.

        Returns:
            BrokerName: First ready broker, or None if no brokers are ready
        """
        try:
            registry = BrokerRegistry()
            registered_brokers = registry.get_registered_brokers()

            for broker_name in registered_brokers:
                if cls.is_broker_ready(broker_name):
                    cls.logger.debug(f"Found ready broker: {broker_name}")
                    return broker_name

            cls.logger.debug("No ready brokers found")
            return None

        except Exception as e:
            cls.logger.warning(f"Error finding ready broker: {str(e)}")
            return None

    @classmethod
    def has_configured_brokers(cls, request: Optional[HttpRequest] = None) -> bool:
        """
        Check if any brokers are configured and enabled with valid credentials,
        OR if the user is currently authenticated with a broker in their session.

        This unifies the logic used in middleware and views.

        Args:
            request: Optional HTTP request to check session authentication

        Returns:
            bool: True if at least one broker is ready or user is authenticated
        """
        try:
            registry = BrokerRegistry()
            registered_brokers = registry.get_registered_brokers()

            for broker_name in registered_brokers:
                try:
                    # 1. Check if user has an active session for this broker (fastest)
                    if request and request.session.get(SessionKeys.get_authenticated_key(broker_name), False):
                        return True

                    # 2. Check if broker is ready (enabled and has valid credentials)
                    if cls.is_broker_ready(broker_name):
                        return True

                except Exception as e:
                    cls.logger.warning(f"Error checking broker {broker_name}: {str(e)}")
                    continue

            return False

        except Exception as e:
            cls.logger.error(f"Error checking configured brokers: {str(e)}")
            return False

    @classmethod
    def clear_broken_session(cls, request: HttpRequest, broker_name: BrokerName) -> None:
        """
        Clear session data for a broker with broken configuration.

        This method provides explicit error handling when a session exists
        but the database configuration is invalid.

        Args:
            request: HTTP request containing session data
            broker_name: Name of the broker to clear session for
        """
        try:
            # Clear authentication session keys
            session_keys_to_clear = [
                SessionKeys.get_authenticated_key(broker_name),
                SessionKeys.get_credentials_key(broker_name),
                f"{broker_name}_session_id",
                f"{broker_name}_last_validated",
                f"{broker_name}_totp_required",
            ]

            cleared_keys = []
            for key in session_keys_to_clear:
                if key in request.session:
                    del request.session[key]
                    cleared_keys.append(key)

            # Save session changes
            if cleared_keys:
                request.session.save()
                cls.logger.info(f"Cleared broken session data for broker {broker_name}: {cleared_keys}")
            else:
                cls.logger.debug(f"No session data to clear for broker {broker_name}")

        except Exception as e:
            cls.logger.error(f"Error clearing session for broker {broker_name}: {str(e)}")
