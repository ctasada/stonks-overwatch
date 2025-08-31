"""
Simple session checker for DeGiroService.

Provides a straightforward way to check if DeGiroService has an active session
before creating UpdateService or performing operations.
"""

from typing import Optional

from stonks_overwatch.utils.core.logger import StonksLogger


class SessionRequiredError(Exception):
    """Raised when an operation requires an active session but none is available."""

    pass


class DeGiroSessionChecker:
    """Simple checker for DeGiroService session availability."""

    logger = StonksLogger.get_logger("stonks_overwatch.session_checker", "[DEGIRO|SESSION_CHECKER]")

    @classmethod
    def get_active_session_id(cls) -> Optional[str]:
        """
        Get the active session ID from DeGiroService singleton.

        Returns:
            str: Session ID if available, None otherwise
        """
        try:
            from stonks_overwatch.services.brokers.degiro.client.degiro_client import DeGiroService

            degiro_service = DeGiroService()

            # Try to get session ID
            session_id = degiro_service.get_session_id()

            if session_id:
                cls.logger.debug(f"Active session found: {session_id[:8]}...")
                return session_id
            else:
                cls.logger.debug("No active session available")
                return None

        except Exception as e:
            cls.logger.debug(f"Cannot get session ID: {e}")
            return None

    @classmethod
    def has_active_session(cls) -> bool:
        """
        Check if DeGiroService has an active session.

        Returns:
            bool: True if active session exists, False otherwise
        """
        return cls.get_active_session_id() is not None

    @classmethod
    def require_active_session(cls) -> str:
        """
        Require an active session, raise exception if not available.

        Returns:
            str: Active session ID

        Raises:
            SessionRequiredError: If no active session is available
        """
        session_id = cls.get_active_session_id()

        if session_id:
            return session_id
        else:
            raise SessionRequiredError("Operation requires an active DeGiro session. Please authenticate first.")
