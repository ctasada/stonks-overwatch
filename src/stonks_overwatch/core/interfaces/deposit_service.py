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

       class MyDepositService(DepositServiceInterface, BaseService):
           def __init__(self, config: Optional[BaseConfig] = None, **kwargs):
               super().__init__(config, **kwargs)
               # Now you can use self.config and self.base_currency
       ```

    3. This maintains backward compatibility while enabling automatic
       configuration injection from the unified factory.
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
