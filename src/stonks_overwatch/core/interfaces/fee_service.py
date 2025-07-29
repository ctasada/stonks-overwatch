"""
Fee service interface.

This module defines the interface for fee service implementations.
This interface is optional - only brokers that support fee tracking
need to implement this interface.
"""

from abc import ABC, abstractmethod
from typing import List

from stonks_overwatch.services.models import Fee


class FeeServiceInterface(ABC):
    """
    Interface for fee service implementations.

    This interface defines the common operations that fee services
    should support. This is an optional interface - only brokers that
    support fee tracking need to implement it.

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

       class MyFeeService(FeeServiceInterface, BaseService):
           def __init__(self, config: Optional[BaseConfig] = None, **kwargs):
               super().__init__(config, **kwargs)
               # Now you can use self.config and self.base_currency
       ```

    3. This maintains backward compatibility while enabling automatic
       configuration injection from the unified factory.
    """

    @abstractmethod
    def get_fees(self) -> List[Fee]:
        """
        Retrieves the fee history including transaction fees, account fees, and other charges.

        Returns:
            List[Fee]: List of fees sorted by date and time (newest first)
        """
        pass
