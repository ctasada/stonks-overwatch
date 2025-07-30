"""
Account service interface.

This module defines the interface for account service implementations.
This interface is optional - only brokers that support account overview
functionality need to implement this interface.
"""

from abc import ABC, abstractmethod
from typing import List

from stonks_overwatch.services.models import AccountOverview


class AccountServiceInterface(ABC):
    """
    Interface for account service implementations.

    This interface defines the common operations that account services
    should support, such as retrieving account overview data including
    transaction history, account changes, and portfolio movements.

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

       class MyAccountService(AccountServiceInterface, BaseService):
           def __init__(self, config: Optional[BaseConfig] = None, **kwargs):
               super().__init__(config, **kwargs)
               # Now you can use self.config and self.base_currency
       ```

    3. This maintains backward compatibility while enabling automatic
       configuration injection from the unified factory.
    """

    @abstractmethod
    def get_account_overview(self) -> List[AccountOverview]:
        """
        Retrieves the account overview including transaction history and account movements.

        Returns:
            List[AccountOverview]: List of account overview entries sorted by date (newest first)
        """
        pass
