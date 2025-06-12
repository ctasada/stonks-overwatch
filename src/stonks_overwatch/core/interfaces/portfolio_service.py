"""
Portfolio service interface.

This module defines the interface for portfolio service implementations.
All broker portfolio services should implement this interface.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from stonks_overwatch.services.models import DailyValue, PortfolioEntry, TotalPortfolio

class PortfolioServiceInterface(ABC):
    """
    Interface for portfolio service implementations.

    This interface defines the common operations that all portfolio services
    should support, such as retrieving portfolio data, calculating totals,
    and providing historical information.
    """

    @property
    @abstractmethod
    def get_portfolio(self) -> List[PortfolioEntry]:
        """
        Retrieves the current portfolio entries.

        Returns:
            List[PortfolioEntry]: List of portfolio entries including stocks,
                ETFs, crypto assets, and cash balances
        """
        pass

    @abstractmethod
    def get_portfolio_total(self, portfolio: Optional[List[PortfolioEntry]] = None) -> TotalPortfolio:
        """
        Calculates the total portfolio summary.

        Args:
            portfolio: Optional portfolio entries. If None, will fetch current portfolio

        Returns:
            TotalPortfolio: Portfolio summary including total value, P&L, ROI, etc.
        """
        pass

    @abstractmethod
    def calculate_historical_value(self) -> List[DailyValue]:
        """
        Calculates the historical portfolio value over time.

        Returns:
            List[DailyValue]: List of daily portfolio values
        """
        pass

    @abstractmethod
    def calculate_product_growth(self) -> dict:
        """
        Calculates the growth history for each product/asset in the portfolio.

        Returns:
            dict: Dictionary mapping product IDs to their historical quantities
        """
        pass
