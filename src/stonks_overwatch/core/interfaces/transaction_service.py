"""
Transaction service interface.

This module defines the interface for transaction service implementations.
All broker transaction services should implement this interface.
"""

from abc import ABC, abstractmethod
from typing import List

from stonks_overwatch.services.models import Transaction

class TransactionServiceInterface(ABC):
    """
    Interface for transaction service implementations.

    This interface defines the common operations that all transaction services
    should support, such as retrieving transaction history and processing
    transaction data.
    """

    @abstractmethod
    def get_transactions(self) -> List[Transaction]:
        """
        Retrieves the transaction history.

        Returns:
            List[Transaction]: List of transactions sorted by date (newest first)
        """
        pass
