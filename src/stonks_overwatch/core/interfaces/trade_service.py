"""
Trades service interface.

This module defines the interface for trade service implementations.
All broker trade services should implement this interface.
"""

from abc import ABC, abstractmethod
from typing import List

from stonks_overwatch.services.models import Trade


class TradeServiceInterface(ABC):
    """
    Interface for trades service implementations.

    This interface defines the common operations that all trade services
    should support, such as retrieving trade history and processing
    trade data.

    **Dependency Injection Support:**

    To support dependency injection with the BrokerFactory, service
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

       class MyTradeService(TradeServiceInterface, BaseService):
           def __init__(self, config: Optional[BaseConfig] = None, **kwargs):
               super().__init__(config, **kwargs)
               # Now you can use self.config and self.base_currency
       ```

    3. This maintains backward compatibility while enabling automatic
       configuration injection from the unified factory.
    """

    @abstractmethod
    def get_trades(self) -> List[Trade]:
        """
        Retrieves the trade history.

        Returns:
            List[Trade]: List of trades sorted by date (newest first)
        """
        pass
