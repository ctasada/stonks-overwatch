"""
Base broker service interface.

This module defines the common interface for broker service implementations.
All broker services should implement this interface to ensure consistency.
"""

from abc import ABC, abstractmethod


class BrokerServiceInterface(ABC):
    """
    Base interface for broker service implementations.

    This interface defines the common operations that all broker services
    should support, such as authentication, connection management, and
    basic service identification.

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

       class MyBrokerService(BrokerServiceInterface, BaseService):
           def __init__(self, config: Optional[BaseConfig] = None, **kwargs):
               super().__init__(config, **kwargs)
               # Now you can use self.config and self.base_currency
       ```

    3. This maintains backward compatibility while enabling automatic
       configuration injection from the unified factory.
    """

    @property
    @abstractmethod
    def broker_name(self) -> str:
        """
        Returns the name of the broker (e.g., 'DeGiro', 'Bitvavo').

        Returns:
            str: The broker name
        """
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """
        Returns whether the broker service is currently connected.

        Returns:
            bool: True if connected, False otherwise
        """
        pass

    @property
    @abstractmethod
    def supports_offline_mode(self) -> bool:
        """
        Returns whether the broker service supports offline mode.

        Returns:
            bool: True if offline mode is supported, False otherwise
        """
        pass

    @abstractmethod
    def connect(self) -> bool:
        """
        Establishes a connection to the broker service.

        Returns:
            bool: True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """
        Closes the connection to the broker service.
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Tests the connection to the broker service.

        Returns:
            bool: True if connection is working, False otherwise
        """
        pass
