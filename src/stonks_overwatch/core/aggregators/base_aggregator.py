"""
Base aggregator class for combining broker data.

This module provides the base class that all aggregators should inherit from,
offering common patterns for broker service management and data aggregation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from stonks_overwatch.config.config import Config
from stonks_overwatch.core.exceptions import DataAggregationException
from stonks_overwatch.core.factories.broker_registry import ServiceType
from stonks_overwatch.core.factories.service_factory import ServiceFactory
from stonks_overwatch.services.brokers.ibkr.client.ibkr_service import IbkrService
from stonks_overwatch.services.models import PortfolioId
from stonks_overwatch.utils.core.logger import StonksLogger


class BaseAggregator(ABC):
    """
    Base class for all data aggregators.

    This class provides common functionality for aggregating data from multiple
    broker sources, including broker service management, configuration handling,
    and error management.
    """

    def __init__(self, service_type: ServiceType):
        """
        Initialize the base aggregator.

        Args:
            service_type: The type of service this aggregator works with
        """
        self._service_type = service_type
        self._service_factory = ServiceFactory()
        self._config = Config.get_global()
        self._logger = StonksLogger.get_logger(
            f"stonks_overwatch.aggregators.{self.__class__.__name__.lower()}",
            f"[AGGREGATOR|{service_type.value.upper()}]",
        )
        self._broker_services: Dict[str, Any] = {}
        self._initialize_broker_services()

    def _initialize_broker_services(self) -> None:
        """
        Initialize broker services based on available brokers and service type.
        """
        available_brokers = self._service_factory.get_available_brokers()

        self._logger.debug(f"Available brokers: {available_brokers}")

        for broker_name in available_brokers:
            if self._service_factory.broker_supports_service(broker_name, self._service_type):
                try:
                    service = self._get_broker_service(broker_name)
                    if service:
                        self._broker_services[broker_name] = service
                        self._logger.debug(f"Initialized {broker_name} {self._service_type.value} service")
                except Exception as e:
                    self._logger.warning(f"Failed to initialize {broker_name} service: {e}")

    def _get_broker_service(self, broker_name: str) -> Optional[Any]:
        """
        Get a broker service instance for the specified broker.

        Args:
            broker_name: Name of the broker

        Returns:
            Service instance if available, None otherwise
        """
        try:
            # For now, create services with proper dependencies manually
            # until we improve the service factory to handle dependencies
            if broker_name == "degiro":
                return self._create_degiro_service()
            elif broker_name == "bitvavo":
                return self._create_bitvavo_service()
            elif broker_name == "ibkr":
                return self._create_ibkr_service()
            else:
                self._logger.error(f"{broker_name} is not supported")
                return None
        except Exception as e:
            self._logger.error(f"Failed to create {self._service_type.value} service for {broker_name}: {e}")
            return None

    def _create_degiro_service(self) -> Optional[Any]:
        """Create DeGiro service with proper dependencies."""
        try:
            from stonks_overwatch.services.brokers.degiro.client.degiro_client import DeGiroService

            degiro_client = DeGiroService()

            if self._service_type == ServiceType.PORTFOLIO:
                from stonks_overwatch.services.brokers.degiro.services.portfolio_service import PortfolioService

                return PortfolioService(degiro_service=degiro_client)
            elif self._service_type == ServiceType.TRANSACTION:
                from stonks_overwatch.services.brokers.degiro.services.transaction_service import TransactionsService

                return TransactionsService(degiro_service=degiro_client)
            elif self._service_type == ServiceType.DEPOSIT:
                from stonks_overwatch.services.brokers.degiro.services.deposit_service import DepositsService

                return DepositsService(degiro_service=degiro_client)
            elif self._service_type == ServiceType.DIVIDEND:
                from stonks_overwatch.services.brokers.degiro.services.account_service import AccountOverviewService
                from stonks_overwatch.services.brokers.degiro.services.currency_service import CurrencyConverterService
                from stonks_overwatch.services.brokers.degiro.services.dividend_service import DividendsService
                from stonks_overwatch.services.brokers.degiro.services.portfolio_service import PortfolioService

                account_service = AccountOverviewService()
                currency_service = CurrencyConverterService()
                portfolio_service = PortfolioService(degiro_service=degiro_client)

                return DividendsService(
                    account_overview=account_service,
                    currency_service=currency_service,
                    degiro_service=degiro_client,
                    portfolio_service=portfolio_service,
                )
            elif self._service_type == ServiceType.FEE:
                from stonks_overwatch.services.brokers.degiro.services.fee_service import FeesService

                return FeesService(degiro_service=degiro_client)
            elif self._service_type == ServiceType.ACCOUNT:
                from stonks_overwatch.services.brokers.degiro.services.account_service import AccountOverviewService

                return AccountOverviewService()
        except Exception as e:
            self._logger.error(f"Failed to create DeGiro {self._service_type.value} service: {e}")
            return None

    def _create_bitvavo_service(self) -> Optional[Any]:
        """Create Bitvavo service with proper dependencies."""
        try:
            if self._service_type == ServiceType.PORTFOLIO:
                from stonks_overwatch.services.brokers.bitvavo.services.portfolio_service import PortfolioService

                return PortfolioService()
            elif self._service_type == ServiceType.TRANSACTION:
                from stonks_overwatch.services.brokers.bitvavo.services.transaction_service import TransactionsService

                return TransactionsService()
            elif self._service_type == ServiceType.DEPOSIT:
                from stonks_overwatch.services.brokers.bitvavo.services.deposit_service import DepositsService

                return DepositsService()
            elif self._service_type == ServiceType.FEE:
                from stonks_overwatch.services.brokers.bitvavo.services.fee_service import FeesService

                return FeesService()
            elif self._service_type == ServiceType.ACCOUNT:
                from stonks_overwatch.services.brokers.bitvavo.services.account_service import AccountOverviewService

                return AccountOverviewService()
            elif self._service_type == ServiceType.DIVIDEND:
                from stonks_overwatch.services.brokers.bitvavo.services.dividends_service import DividendsService

                return DividendsService()
        except Exception as e:
            self._logger.error(f"Failed to create Bitvavo {self._service_type.value} service: {e}")
            return None

    def _create_ibkr_service(self) -> Optional[Any]:
        """Create IBKR service with proper dependencies."""
        try:
            if self._service_type == ServiceType.PORTFOLIO:
                from stonks_overwatch.services.brokers.ibkr.services.portfolio import PortfolioService

                return PortfolioService()
            elif self._service_type == ServiceType.TRANSACTION:
                from stonks_overwatch.services.brokers.ibkr.services.transactions import TransactionsService

                ibkr_service = IbkrService()
                return TransactionsService(ibkr_service=ibkr_service)
            elif self._service_type == ServiceType.DEPOSIT:
                return None
            elif self._service_type == ServiceType.FEE:
                return None
            elif self._service_type == ServiceType.ACCOUNT:
                from stonks_overwatch.services.brokers.ibkr.services.account_overview import AccountOverviewService

                return AccountOverviewService()
            elif self._service_type == ServiceType.DIVIDEND:
                from stonks_overwatch.services.brokers.ibkr.services.dividends import DividendsService

                ibkr_service = IbkrService()

                return DividendsService(ibkr_service=ibkr_service)
        except Exception as e:
            self._logger.error(f"Failed to create IBKR {self._service_type.value} service: {e}", exc_info=True)
            return None

    def _is_broker_enabled(self, broker_name: str, selected_portfolio: PortfolioId) -> bool:
        """
        Check if a broker is enabled for the selected portfolio.

        Args:
            broker_name: Name of the broker to check
            selected_portfolio: Selected portfolio configuration

        Returns:
            True if broker is enabled, False otherwise
        """
        self._logger.debug(f"Checking if {broker_name} enabled for {selected_portfolio}")
        if broker_name == "degiro":
            return self._config.is_degiro_enabled(selected_portfolio)
        elif broker_name == "bitvavo":
            return self._config.is_bitvavo_enabled(selected_portfolio)
        elif broker_name == "ibkr":
            return self._config.is_ibkr_enabled(selected_portfolio)
        else:
            # For other brokers, assume they're enabled if they have services
            return broker_name in self._broker_services

    def _get_enabled_brokers(self, selected_portfolio: PortfolioId) -> List[str]:
        """
        Get the list of brokers that are enabled for the selected portfolio.

        Args:
            selected_portfolio: Selected portfolio configuration

        Returns:
            List of enabled broker names
        """
        self._logger.debug(f"Getting enabled brokers for {selected_portfolio}")
        self._logger.debug(f"Brokers: {list(self._broker_services.keys())}")
        return [
            broker_name
            for broker_name in self._broker_services.keys()
            if self._is_broker_enabled(broker_name, selected_portfolio)
        ]

    def _collect_broker_data(
        self, selected_portfolio: PortfolioId, method_name: str, *args, **kwargs
    ) -> Dict[str, Any]:
        """
        Collect data from all enabled brokers using the specified method.

        Args:
            selected_portfolio: Selected portfolio configuration
            method_name: Name of the method to call on each broker service
            *args: Arguments to pass to the method
            **kwargs: Keyword arguments to pass to the method

        Returns:
            Dictionary mapping broker names to their data

        Raises:
            DataAggregationException: If data collection fails
        """
        enabled_brokers = self._get_enabled_brokers(selected_portfolio)
        if not enabled_brokers:
            raise DataAggregationException("Failed to find any enabled broker")

        broker_data = {}
        broker_errors = {}
        first_exc = None
        first_tb = None

        for broker_name in enabled_brokers:
            try:
                service = self._broker_services[broker_name]
                if hasattr(service, method_name):
                    attr = getattr(service, method_name)

                    # Check if it's a property or callable
                    if callable(attr):
                        # It's a method, call it with arguments
                        data = attr(*args, **kwargs)
                    else:
                        # It's a property, just use the value
                        data = attr

                    broker_data[broker_name] = data
                    self._logger.debug(f"Collected data from {broker_name} using {method_name}")
                else:
                    self._logger.warning(f"{broker_name} service does not have method {method_name}")
            except Exception as e:
                self._logger.error(f"Failed to collect data from {broker_name}: {e}")
                broker_errors[broker_name] = str(e)
                if first_exc is None:
                    first_exc = e
                    first_tb = e.__traceback__
                # Don't raise here - continue with other brokers

        if not broker_data:
            if first_exc is not None:
                raise DataAggregationException(
                    f"No data collected from any broker for {method_name}. Errors: {broker_errors}"
                ).with_traceback(first_tb)
            else:
                raise DataAggregationException(
                    f"No data collected from any broker for {method_name}. Errors: {broker_errors}"
                )

        return broker_data

    def _merge_lists(self, data_lists: List[List[Any]]) -> List[Any]:
        """
        Merge multiple lists into a single list.

        Args:
            data_lists: List of lists to merge

        Returns:
            Merged list containing all items
        """
        merged = []
        for data_list in data_lists:
            if data_list:
                merged.extend(data_list)
        return merged

    def _sum_numeric_values(self, values: List[Union[int, float]]) -> float:
        """
        Sum numeric values with error handling.

        Args:
            values: List of numeric values to sum

        Returns:
            Sum of all values
        """
        return sum(float(value) for value in values if value is not None)

    @property
    def supported_brokers(self) -> List[str]:
        """
        Get the list of brokers supported by this aggregator.

        Returns:
            List of supported broker names
        """
        return list(self._broker_services.keys())

    @property
    def service_type(self) -> ServiceType:
        """
        Get the service type this aggregator works with.

        Returns:
            Service type enum value
        """
        return self._service_type

    @abstractmethod
    def aggregate_data(self, selected_portfolio: PortfolioId, **kwargs) -> Any:
        """
        Aggregate data from all enabled brokers.

        This method must be implemented by subclasses to define their specific
        aggregation logic.

        Args:
            selected_portfolio: Selected portfolio configuration
            **kwargs: Additional arguments specific to the aggregator

        Returns:
            Aggregated data in the appropriate format
        """
        pass

    def _collect_and_merge_lists(
        self, selected_portfolio: PortfolioId, method_name: str, merger_func=None, *args, **kwargs
    ) -> List[Any]:
        """
        Collect data from brokers, combine into a single list, and optionally merge.

        This is a common pattern for collecting list-based data (portfolios, transactions, etc.)

        Args:
            selected_portfolio: Selected portfolio configuration
            method_name: Name of the method to call on each broker service
            merger_func: Optional function to merge the combined data
            *args: Arguments to pass to the method
            **kwargs: Keyword arguments to pass to the method

        Returns:
            Combined (and optionally merged) list of data
        """
        broker_data = self._collect_broker_data(selected_portfolio, method_name, *args, **kwargs)

        # Combine all data into a single list
        combined_data = []
        for broker_name, data in broker_data.items():
            if isinstance(data, list):
                combined_data.extend(data)
            else:
                # Handle property-style access or other formats
                try:
                    combined_data.extend(data)
                except (TypeError, AttributeError):
                    self._logger.warning(f"Unexpected data format from {broker_name}: {type(data)}")

        # Apply merger function if provided
        if merger_func and combined_data:
            return merger_func(combined_data)

        return combined_data

    def _collect_and_merge_objects(
        self, selected_portfolio: PortfolioId, method_name: str, expected_type: type, merger_func=None, *args, **kwargs
    ) -> Any:
        """
        Collect objects of a specific type from brokers and optionally merge them.

        This is a common pattern for collecting typed objects (TotalPortfolio, etc.)

        Args:
            selected_portfolio: Selected portfolio configuration
            method_name: Name of the method to call on each broker service
            expected_type: Expected type of the returned objects
            merger_func: Optional function to merge the collected objects
            *args: Arguments to pass to the method
            **kwargs: Keyword arguments to pass to the method

        Returns:
            Merged object or list of objects
        """
        broker_data = self._collect_broker_data(selected_portfolio, method_name, *args, **kwargs)

        # Collect objects of the expected type
        typed_objects = []
        for broker_name, data in broker_data.items():
            if isinstance(data, expected_type):
                typed_objects.append(data)
            else:
                self._logger.warning(
                    f"Unexpected data type from {broker_name}: expected {expected_type.__name__}, got {type(data)}"
                )

        # Apply merger function if provided and we have data
        if merger_func and typed_objects:
            return merger_func(typed_objects)

        return typed_objects

    def _collect_and_sort(
        self,
        selected_portfolio: PortfolioId,
        method_name: str,
        sort_key=None,
        reverse: bool = False,
        merger_func=None,
        *args,
        **kwargs,
    ) -> List[Any]:
        """
        Collect data from brokers, combine, optionally merge, and sort.

        Common pattern for data that needs to be sorted (transactions by date, etc.)

        Args:
            selected_portfolio: Selected portfolio configuration
            method_name: Name of the method to call on each broker service
            sort_key: Function to use for sorting (optional)
            reverse: Whether to sort in reverse order
            merger_func: Optional function to merge the combined data
            *args: Arguments to pass to the method
            **kwargs: Keyword arguments to pass to the method

        Returns:
            Combined, merged, and sorted list of data
        """
        combined_data = self._collect_and_merge_lists(selected_portfolio, method_name, merger_func, *args, **kwargs)

        if sort_key:
            return sorted(combined_data, key=sort_key, reverse=reverse)
        else:
            return sorted(combined_data, reverse=reverse)
