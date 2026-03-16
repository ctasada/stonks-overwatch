"""
Trading journal service interface.

This module defines the interface for trading journal service implementations.
All broker trading journal services should implement this interface.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from stonks_overwatch.services.models import AccountSummary, Trade


class TradingJournalServiceInterface(ABC):
    @abstractmethod
    def get_closed_trades(self) -> List[Trade]:
        pass

    def get_account_summary(self) -> Optional[AccountSummary]:
        """Return an account summary snapshot, or None if not supported by this broker."""
        return None
