"""
Broker service registry.

This module provides a registry for managing available broker services
and their capabilities.
"""

from enum import Enum
from typing import Dict, List, Optional, Type

from stonks_overwatch.core.exceptions import ServiceRegistryException
from stonks_overwatch.core.interfaces.deposit_service import DepositServiceInterface
from stonks_overwatch.core.interfaces.dividend_service import DividendServiceInterface
from stonks_overwatch.core.interfaces.portfolio_service import PortfolioServiceInterface
from stonks_overwatch.core.interfaces.transaction_service import TransactionServiceInterface
from stonks_overwatch.utils.core.singleton import singleton


class ServiceType(Enum):
    """Enumeration of available service types."""

    PORTFOLIO = "portfolio"
    TRANSACTION = "transaction"
    DEPOSIT = "deposit"
    DIVIDEND = "dividend"
    FEE = "fee"
    ACCOUNT = "account"


@singleton
class BrokerRegistry:
    """
    Registry for managing broker services and their capabilities.

    This singleton class maintains a registry of available brokers
    and their supported services.
    """

    def __init__(self):
        self._brokers: Dict[str, Dict[str, Type]] = {}
        self._broker_capabilities: Dict[str, List[ServiceType]] = {}

    def register_broker(
        self,
        broker_name: str,
        portfolio_service: Type[PortfolioServiceInterface],
        transaction_service: Optional[Type[TransactionServiceInterface]] = None,
        deposit_service: Optional[Type[DepositServiceInterface]] = None,
        dividend_service: Optional[Type[DividendServiceInterface]] = None,
        fee_service: Optional[Type] = None,
        account_service: Optional[Type] = None,
    ) -> None:
        """
        Register a broker and its services.

        Args:
            broker_name: Name of the broker (e.g., 'degiro', 'bitvavo')
            portfolio_service: Portfolio service class
            transaction_service: Transaction service class
            deposit_service: Deposit service class
            dividend_service: Optional dividend service class
            fee_service: Optional fee service class
            account_service: Optional account service class

        Raises:
            ServiceRegistryException: If broker is already registered
        """
        if broker_name in self._brokers:
            raise ServiceRegistryException(f"Broker '{broker_name}' is already registered")

        services = {
            ServiceType.PORTFOLIO.value: portfolio_service,
            ServiceType.TRANSACTION.value: transaction_service,
            ServiceType.DEPOSIT.value: deposit_service,
        }

        capabilities = [ServiceType.PORTFOLIO, ServiceType.TRANSACTION, ServiceType.DEPOSIT]

        if dividend_service:
            services[ServiceType.DIVIDEND.value] = dividend_service
            capabilities.append(ServiceType.DIVIDEND)

        if fee_service:
            services[ServiceType.FEE.value] = fee_service
            capabilities.append(ServiceType.FEE)

        if account_service:
            services[ServiceType.ACCOUNT.value] = account_service
            capabilities.append(ServiceType.ACCOUNT)

        self._brokers[broker_name] = services
        self._broker_capabilities[broker_name] = capabilities

    def get_broker_service(self, broker_name: str, service_type: ServiceType) -> Optional[Type]:
        """
        Get a service class for a specific broker.

        Args:
            broker_name: Name of the broker
            service_type: Type of service to retrieve

        Returns:
            Service class if available, None otherwise
        """
        broker_services = self._brokers.get(broker_name)
        if not broker_services:
            return None

        return broker_services.get(service_type.value)

    def get_available_brokers(self) -> List[str]:
        """
        Get the list of all registered brokers.

        Returns:
            List of broker names
        """
        return list(self._brokers.keys())

    def get_broker_capabilities(self, broker_name: str) -> List[ServiceType]:
        """
        Get the capabilities of a specific broker.

        Args:
            broker_name: Name of the broker

        Returns:
            List of supported service types
        """
        return self._broker_capabilities.get(broker_name, [])

    def broker_supports_service(self, broker_name: str, service_type: ServiceType) -> bool:
        """
        Check if a broker supports a specific service type.

        Args:
            broker_name: Name of the broker
            service_type: Type of service to check

        Returns:
            True if broker supports the service, False otherwise
        """
        capabilities = self.get_broker_capabilities(broker_name)
        return service_type in capabilities

    def unregister_broker(self, broker_name: str) -> None:
        """
        Unregister a broker from the registry.

        Args:
            broker_name: Name of the broker to unregister
        """
        self._brokers.pop(broker_name, None)
        self._broker_capabilities.pop(broker_name, None)
