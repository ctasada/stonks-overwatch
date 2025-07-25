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

       class MyDividendService(DividendServiceInterface, BaseService):
           def __init__(self, config: Optional[BaseConfig] = None, **kwargs):
               super().__init__(config, **kwargs)
               # Now you can use self.config and self.base_currency
       ```

    3. This maintains backward compatibility while enabling automatic
       configuration injection from the unified factory.
    """

    @abstractmethod
    def get_dividends(self) -> List[Dividend]:
        """
        Retrieves the dividend history including paid, announced, and forecasted dividends.

        Returns:
            List[Dividend]: List of dividends sorted by payment date
        """
        pass
