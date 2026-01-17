"""
Demo mode detection utility for Stonks Overwatch.

This module provides utilities to detect if the application is running in demo mode.
"""

import functools
import os

from stonks_overwatch.utils.core.logger import StonksLogger

logger = StonksLogger.get_logger(__name__, "[DEMO_MODE]")


@functools.lru_cache(maxsize=1)
def is_demo_mode() -> bool:
    """
    Check if the application is running in demo mode.

    Demo mode is detected by checking the DEMO_MODE environment variable.

    The result is cached using functools.lru_cache to improve performance since this
    function may be called multiple times during a request lifecycle.

    To clear the cache (e.g., after changing DEMO_MODE at runtime), call:
    is_demo_mode.cache_clear()

    Returns:
        True if demo mode is active, False otherwise
    """
    try:
        # Direct check of DEMO_MODE environment variable
        demo_mode_env = os.getenv("DEMO_MODE", "False")
        if demo_mode_env.lower() in ["true", "1", "yes"]:
            logger.debug("Demo mode detected via DEMO_MODE environment variable")
            return True

        logger.debug("Demo mode not active")
        return False

    except Exception as e:
        logger.error(f"Error checking demo mode: {str(e)}")
        return False
