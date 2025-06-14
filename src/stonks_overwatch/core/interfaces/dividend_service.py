"""
Dividend service interface.

This module defines the interface for dividend service implementations.
This interface is optional - only brokers that support dividend-paying
assets need to implement this interface.
"""

from abc import ABC, abstractmethod
from typing import List

from stonks_overwatch.services.models import Dividend


class DividendServiceInterface(ABC):
    """
    Interface for dividend service implementations.

    This interface defines the common operations that dividend services
    should support. This is an optional interface - only brokers that
    support dividend-paying assets need to implement it.
    """

    @abstractmethod
    def get_dividends(self) -> List[Dividend]:
        """
        Retrieves the dividend history including paid, announced, and forecasted dividends.

        Returns:
            List[Dividend]: List of dividends sorted by payment date
        """
        pass
