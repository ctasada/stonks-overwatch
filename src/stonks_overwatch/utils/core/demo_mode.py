"""
Demo mode detection utility for Stonks Overwatch.

This module provides utilities to detect if the application is running in demo mode.
"""

import os

from stonks_overwatch.utils.core.logger import StonksLogger

logger = StonksLogger.get_logger(__name__, "[DEMO_MODE]")


def is_demo_mode() -> bool:
    """
    Check if the application is running in demo mode.

    Demo mode is detected by checking if any broker has offline_mode enabled,
    which happens when DEMO_MODE environment variable is set.

    Returns:
        True if demo mode is active, False otherwise
    """
    try:
        # Direct check of DEMO_MODE environment variable
        demo_mode_env = os.getenv("DEMO_MODE", "False")
        if demo_mode_env.lower() in ["true", "1", "yes"]:
            logger.debug("Demo mode detected via DEMO_MODE environment variable")
            return True

        # Also check if any broker config has offline_mode enabled
        # This covers cases where demo mode was activated programmatically
        return _check_broker_offline_mode()

    except Exception as e:
        logger.error(f"Error checking demo mode: {str(e)}")
        return False


def _check_broker_offline_mode() -> bool:
    """
    Check if any broker configuration has offline_mode enabled.

    Returns:
        True if any broker has offline_mode enabled, False otherwise
    """
    try:
        from stonks_overwatch.core.factories.broker_factory import BrokerFactory
        from stonks_overwatch.core.factories.broker_registry import BrokerRegistry

        registry = BrokerRegistry()
        factory = BrokerFactory()
        registered_brokers = registry.get_registered_brokers()

        for broker_name in registered_brokers:
            try:
                config = factory.create_config(broker_name)
                if config and hasattr(config, "offline_mode") and config.offline_mode:
                    logger.debug(f"Demo mode detected via {broker_name} offline_mode")
                    return True
            except Exception as e:
                logger.warning(f"Error checking offline mode for {broker_name}: {str(e)}")
                continue

        return False

    except Exception as e:
        logger.error(f"Error checking broker offline modes: {str(e)}")
        return False
