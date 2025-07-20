import os
import time as core_time
from abc import ABC, abstractmethod
from typing import Optional

from django.db.utils import OperationalError

from stonks_overwatch.settings import STONKS_OVERWATCH_DATA_DIR
from stonks_overwatch.utils.core.logger import StonksLogger


class AbstractUpdateService(ABC):
    def __init__(
        self,
        broker_name: str,
        import_folder: Optional[str] = None,
        debug_mode: Optional[bool] = None,
    ):
        """
        Initialize the UpdateService.

        Args:
            broker_name: Name of the broker (e.g., 'bitvavo', 'ibkr', 'degiro')
            import_folder: Folder to store JSON files for debugging purposes
            debug_mode: If True, the service will store JSON files for debugging
        """
        self.broker_name = broker_name.lower()
        self.import_folder = (
            import_folder
            if import_folder is not None
            else os.path.join(STONKS_OVERWATCH_DATA_DIR, "import", self.broker_name)
        )
        self.debug_mode = (
            debug_mode if debug_mode is not None else os.getenv("DEBUG_MODE", False) in [True, "true", "True", "1"]
        )

        # Create import folder if it doesn't exist
        if not os.path.exists(self.import_folder):
            os.makedirs(self.import_folder)

        # Initialize logger with broker-specific prefix
        logger_name = f"stonks_overwatch.{self.broker_name}.update_service"
        logger_prefix = f"[{self.broker_name.upper()}|UPDATE]"
        self.logger = StonksLogger.get_logger(logger_name, logger_prefix)

    def _log_message(self, message: str) -> None:
        """Log a message to the console."""
        if self.debug_mode:
            self.logger.info(f"[Debug Mode] {message}")
        else:
            self.logger.info(message)

    def _retry_database_operation(self, operation, *args, max_retries=3, delay=0.1, **kwargs):
        """
        Retry a database operation if it fails due to database lock.

        Args:
            operation: A callable that performs the database operation
            *args: Positional arguments to pass to the operation
            max_retries: Maximum number of retry attempts
            delay: Initial delay between retries (will be doubled each time)
            **kwargs: Keyword arguments to pass to the operation

        Returns:
            The result of the operation

        Raises:
            The last exception if all retries fail
        """
        last_exception = None
        current_delay = delay

        for attempt in range(max_retries + 1):
            try:
                return operation(*args, **kwargs)
            except OperationalError as e:
                last_exception = e
                if "database is locked" in str(e).lower() and attempt < max_retries:
                    self.logger.warning(
                        "Database locked, retrying in %.2f seconds (attempt %d/%d)",
                        current_delay,
                        attempt + 1,
                        max_retries,
                    )
                    core_time.sleep(current_delay)
                    current_delay *= 2  # Exponential backoff
                else:
                    raise

        raise last_exception

    @abstractmethod
    def update_all(self):
        pass
