"""
Trading journal service interface.

This module defines the interface for trading journal service implementations.
All broker trading journal services should implement this interface.
"""

from abc import ABC, abstractmethod
from typing import List

from stonks_overwatch.services.models import Trade


class TradingJournalServiceInterface(ABC):
    @abstractmethod
    def get_closed_trades(self) -> List[Trade]:
        pass
