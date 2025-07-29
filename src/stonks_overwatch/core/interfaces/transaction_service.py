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

       class MyTransactionService(TransactionServiceInterface, BaseService):
           def __init__(self, config: Optional[BaseConfig] = None, **kwargs):
               super().__init__(config, **kwargs)
               # Now you can use self.config and self.base_currency
       ```

    3. This maintains backward compatibility while enabling automatic
       configuration injection from the unified factory.
    """

    @abstractmethod
    def get_transactions(self) -> List[Transaction]:
        """
        Retrieves the transaction history.

        Returns:
            List[Transaction]: List of transactions sorted by date (newest first)
        """
        pass
