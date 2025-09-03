import time
from typing import Any, Callable

from stonks_overwatch.services.brokers.degiro.client.degiro_client import DeGiroOfflineModeError
from stonks_overwatch.utils.core.logger import StonksLogger


def is_non_tradeable_product(product: dict) -> bool:
    """Check if the product is non-tradeable.

    This method checks if the product is a non-tradeable product.
    Non-tradeable products are identified by the presence of "Non-tradeable" in the name.

    If the product is NOT tradable, we shouldn't consider it for Growth.

    The 'tradable' attribute identifies old Stocks, like the ones that are
    renamed for some reason, and it's not good enough to identify stocks
    that are provided as dividends, for example.
    """
    if product["symbol"].endswith(".D"):
        # This is a DeGiro-specific symbol, which is not tradeable
        return True

    return "Non tradeable" in product["name"]


def retry_with_backoff(
    func: Callable[[], Any],
    max_retries: int = 3,
    delay_ms: int = 500,
    operation_name: str = "operation",
    logger: StonksLogger = None,
) -> Any:
    """
    Retry a function with exponential backoff.

    Args:
        func: The function to retry
        max_retries: Maximum number of retry attempts (default: 3)
        delay_ms: Initial delay in milliseconds (default: 500ms)
        operation_name: Name of the operation for logging purposes
        logger: Logger instance to use for logging (optional)

    Returns:
        The result of the successful function call, or None if all retries fail
    """
    # Use a default logger if none provided
    if logger is None:
        logger = StonksLogger.get_logger("stonks_overwatch.degiro.helper", "[DEGIRO|RETRY]")

    for attempt in range(max_retries + 1):  # +1 for initial attempt
        try:
            result = func()
            if result is not None:
                if attempt > 0:
                    logger.info(f"Successfully retrieved {operation_name} after {attempt} retries")
                return result
            else:
                if attempt < max_retries:
                    logger.warning(f"{operation_name} returned None, attempt {attempt + 1}/{max_retries + 1}")
                else:
                    logger.warning(f"{operation_name} returned None after all {max_retries + 1} attempts")
        except (ConnectionError, TimeoutError, DeGiroOfflineModeError) as e:
            if attempt < max_retries:
                delay_seconds = delay_ms / 1000.0
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} for {operation_name} failed: {e}. "
                    f"Retrying in {delay_seconds}s..."
                )
                time.sleep(delay_seconds)
                delay_ms *= 2  # Exponential backoff
            else:
                logger.error(f"All {max_retries + 1} attempts for {operation_name} failed: {e}")
                return None
        except Exception as e:
            logger.error(f"Unexpected error during {operation_name}: {e}")
            return None

    return None
