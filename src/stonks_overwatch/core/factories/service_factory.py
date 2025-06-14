"""
Service factory for creating broker service instances.

This module provides a factory for creating instances of broker services
using the broker registry.
"""

from typing import Any, Dict, Optional

from stonks_overwatch.core.exceptions import ServiceFactoryException
from stonks_overwatch.core.factories.broker_registry import BrokerRegistry, ServiceType
from stonks_overwatch.core.interfaces.deposit_service import DepositServiceInterface
from stonks_overwatch.core.interfaces.dividend_service import DividendServiceInterface
from stonks_overwatch.core.interfaces.portfolio_service import PortfolioServiceInterface
from stonks_overwatch.core.interfaces.transaction_service import TransactionServiceInterface
from stonks_overwatch.utils.core.singleton import singleton


@singleton
class ServiceFactory:
    """
    Factory for creating broker service instances.

    This singleton factory uses the broker registry to create instances
    of broker services with proper dependency injection.
    """

    def __init__(self):
        self._registry = BrokerRegistry()
        self._service_instances: Dict[str, Dict[str, Any]] = {}

    def create_portfolio_service(self, broker_name: str, **kwargs) -> PortfolioServiceInterface:
        """
        Create a portfolio service instance for the specified broker.

        Args:
            broker_name: Name of the broker
            **kwargs: Additional arguments to pass to service constructor

        Returns:
            Portfolio service instance

        Raises:
            ServiceFactoryException: If broker doesn't support portfolio service
        """
        service_class = self._registry.get_broker_service(broker_name, ServiceType.PORTFOLIO)
        if not service_class:
            raise ServiceFactoryException(f"Broker '{broker_name}' does not support portfolio service")

        return self._create_service(broker_name, ServiceType.PORTFOLIO, service_class, **kwargs)

    def create_transaction_service(self, broker_name: str, **kwargs) -> TransactionServiceInterface:
        """
        Create a transaction service instance for the specified broker.

        Args:
            broker_name: Name of the broker
            **kwargs: Additional arguments to pass to service constructor

        Returns:
            Transaction service instance

        Raises:
            ServiceFactoryException: If broker doesn't support transaction service
        """
        service_class = self._registry.get_broker_service(broker_name, ServiceType.TRANSACTION)
        if not service_class:
            raise ServiceFactoryException(f"Broker '{broker_name}' does not support transaction service")

        return self._create_service(broker_name, ServiceType.TRANSACTION, service_class, **kwargs)

    def create_deposit_service(self, broker_name: str, **kwargs) -> DepositServiceInterface:
        """
        Create a deposit service instance for the specified broker.

        Args:
            broker_name: Name of the broker
            **kwargs: Additional arguments to pass to service constructor

        Returns:
            Deposit service instance

        Raises:
            ServiceFactoryException: If broker doesn't support deposit service
        """
        service_class = self._registry.get_broker_service(broker_name, ServiceType.DEPOSIT)
        if not service_class:
            raise ServiceFactoryException(f"Broker '{broker_name}' does not support deposit service")

        return self._create_service(broker_name, ServiceType.DEPOSIT, service_class, **kwargs)

    def create_dividend_service(self, broker_name: str, **kwargs) -> Optional[DividendServiceInterface]:
        """
        Create a dividend service instance for the specified broker.

        Args:
            broker_name: Name of the broker
            **kwargs: Additional arguments to pass to service constructor

        Returns:
            Dividend service instance if supported, None otherwise
        """
        service_class = self._registry.get_broker_service(broker_name, ServiceType.DIVIDEND)
        if not service_class:
            return None

        return self._create_service(broker_name, ServiceType.DIVIDEND, service_class, **kwargs)

    def create_fee_service(self, broker_name: str, **kwargs) -> Optional[Any]:
        """
        Create a fee service instance for the specified broker.

        Args:
            broker_name: Name of the broker
            **kwargs: Additional arguments to pass to service constructor

        Returns:
            Fee service instance if supported, None otherwise
        """
        service_class = self._registry.get_broker_service(broker_name, ServiceType.FEE)
        if not service_class:
            return None

        return self._create_service(broker_name, ServiceType.FEE, service_class, **kwargs)

    def create_account_service(self, broker_name: str, **kwargs) -> Optional[Any]:
        """
        Create an account service instance for the specified broker.

        Args:
            broker_name: Name of the broker
            **kwargs: Additional arguments to pass to service constructor

        Returns:
            Account service instance if supported, None otherwise
        """
        service_class = self._registry.get_broker_service(broker_name, ServiceType.ACCOUNT)
        if not service_class:
            return None

        return self._create_service(broker_name, ServiceType.ACCOUNT, service_class, **kwargs)

    def get_available_brokers(self) -> list[str]:
        """
        Get the list of available brokers.

        Returns:
            List of registered broker names
        """
        return self._registry.get_available_brokers()

    def broker_supports_service(self, broker_name: str, service_type: ServiceType) -> bool:
        """
        Check if a broker supports a specific service type.

        Args:
            broker_name: Name of the broker
            service_type: Type of service to check

        Returns:
            True if broker supports the service, False otherwise
        """
        return self._registry.broker_supports_service(broker_name, service_type)

    def _create_service(self, broker_name: str, service_type: ServiceType, service_class: type, **kwargs) -> Any:
        """
        Create a service instance with caching support.

        Args:
            broker_name: Name of the broker
            service_type: Type of service
            service_class: Service class to instantiate
            **kwargs: Additional arguments for service constructor

        Returns:
            Service instance
        """
        # Create cache key
        cache_key = f"{broker_name}_{service_type.value}"

        # Check if instance already exists
        if broker_name not in self._service_instances:
            self._service_instances[broker_name] = {}

        if cache_key not in self._service_instances[broker_name]:
            try:
                # Create new instance
                instance = service_class(**kwargs)
                self._service_instances[broker_name][cache_key] = instance
            except Exception as e:
                raise ServiceFactoryException(
                    f"Failed to create {service_type.value} service for broker '{broker_name}': {e}"
                ) from e

        return self._service_instances[broker_name][cache_key]

    def clear_cache(self, broker_name: Optional[str] = None) -> None:
        """
        Clear the service instance cache.

        Args:
            broker_name: Optional broker name. If provided, only clears cache for that broker.
                        If None, clears all cached instances.
        """
        if broker_name:
            self._service_instances.pop(broker_name, None)
        else:
            self._service_instances.clear()
