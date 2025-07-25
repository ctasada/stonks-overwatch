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

    **Dependency Injection Support:**

    To support dependency injection with the UnifiedBrokerFactory, service
    implementations should:

    1. Accept an optional `config` parameter in their constructor:
       ```python
       def __init__(self, config: Optional[BaseConfig] = None, **kwargs):
           # Implementation specific initialization
       ```

    2. Use the DependencyInjectionMixin or BaseService for automatic
       configuration handling:
       ```python
       from stonks_overwatch.core.interfaces.base_service import BaseService

       class MyPortfolioService(PortfolioServiceInterface, BaseService):
           def __init__(self, config: Optional[BaseConfig] = None, **kwargs):
               super().__init__(config, **kwargs)
               # Now you can use self.config and self.base_currency
       ```

    3. This maintains backward compatibility while enabling automatic
       configuration injection from the unified factory.
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
