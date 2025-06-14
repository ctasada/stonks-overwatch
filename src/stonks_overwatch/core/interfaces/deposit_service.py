"""
Deposit service interface.

This module defines the interface for deposit service implementations.
All broker deposit services should implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, List

from stonks_overwatch.services.models import Deposit


class DepositServiceInterface(ABC):
    """
    Interface for deposit service implementations.

    This interface defines the common operations that all deposit services
    should support, such as retrieving cash deposits/withdrawals and
    calculating cash account values over time.
    """

    @abstractmethod
    def get_cash_deposits(self) -> List[Deposit]:
        """
        Retrieves the cash deposit and withdrawal history.

        Returns:
            List[Deposit]: List of deposits and withdrawals sorted by date (newest first)
        """
        pass

    @abstractmethod
    def calculate_cash_account_value(self) -> Dict[str, float]:
        """
        Calculates the cash account value over time.

        Returns:
            Dict[str, float]: Dictionary mapping date strings (YYYY-MM-DD) to cash balance values
        """
        pass
