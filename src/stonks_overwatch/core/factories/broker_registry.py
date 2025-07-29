"""
Broker registry for managing broker configurations and services.

This module provides a centralized registry for broker configurations and services,
supporting registration, validation, and service creation capabilities.
"""

import threading
from typing import Any, Dict, List, Optional, Type

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.core.exceptions import ServiceFactoryException
from stonks_overwatch.core.service_types import ServiceType
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.core.singleton import singleton


class BrokerRegistryValidationError(ServiceFactoryException):
    """Exception raised when broker registry validation fails."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


@singleton
class BrokerRegistry:
    """
    Centralized registry for managing broker configurations and services.

    This registry provides a unified way to manage broker configurations and
    service classes, supporting registration, validation, and retrieval operations.
    """

    def __init__(self):
        """
        Initialize the broker registry.

        Sets up empty dictionaries for managing broker configurations and services,
        and initializes logging for registry operations.
        """
        self._config_classes: Dict[str, Type[BaseConfig]] = {}
        self._service_classes: Dict[str, Dict[ServiceType, Type]] = {}
        self._broker_capabilities: Dict[str, List[ServiceType]] = {}
        self._lock = threading.RLock()

        self.logger = StonksLogger.get_logger("stonks_overwatch.core", "[BROKER_REGISTRY]")

    def register_broker_config(self, broker_name: str, config_class: Type[BaseConfig]) -> None:
        """
        Register a broker configuration class.

        Args:
            broker_name: Name of the broker
            config_class: Configuration class for the broker

        Raises:
            BrokerRegistryValidationError: If validation fails
        """
        with self._lock:
            self._validate_broker_name(broker_name)
            self._validate_config_class(config_class)

            if broker_name in self._config_classes:
                raise BrokerRegistryValidationError(f"Configuration for broker '{broker_name}' is already registered")

            self._config_classes[broker_name] = config_class
            self.logger.info(f"Registered configuration for broker: {broker_name}")

    def get_config_class(self, broker_name: str) -> Optional[Type[BaseConfig]]:
        """
        Get configuration class for a broker.

        Args:
            broker_name: Name of the broker

        Returns:
            Configuration class if found, None otherwise
        """
        return self._config_classes.get(broker_name)

    def is_config_registered(self, broker_name: str) -> bool:
        """
        Check if a broker configuration is registered.

        Args:
            broker_name: Name of the broker

        Returns:
            True if configuration is registered, False otherwise
        """
        return broker_name in self._config_classes

    def register_broker_services(self, broker_name: str, **services) -> None:
        """
        Register broker service classes.

        Args:
            broker_name: Name of the broker
            **services: Service classes keyed by service type name

        Raises:
            BrokerRegistryValidationError: If validation fails
        """
        with self._lock:
            self._validate_broker_name(broker_name)

            if not services:
                raise BrokerRegistryValidationError("At least one service must be provided")

            if broker_name in self._service_classes:
                raise BrokerRegistryValidationError(f"Services for broker '{broker_name}' are already registered")

            # Validate and convert service names to ServiceType enum
            service_dict = {}
            for service_name, service_class in services.items():
                service_type = self._validate_service_type(service_name)
                self._validate_service_class(service_class)
                service_dict[service_type] = service_class

            # Validate required services (portfolio is always required)
            required_services = {ServiceType.PORTFOLIO}
            provided_services = set(service_dict.keys())

            if not required_services.issubset(provided_services):
                missing_services = required_services - provided_services
                raise BrokerRegistryValidationError(
                    f"Missing required services for broker '{broker_name}': {[s.value for s in missing_services]}"
                )

            self._service_classes[broker_name] = service_dict
            self._broker_capabilities[broker_name] = list(service_dict.keys())

            service_list = [service_type.value for service_type in service_dict.keys()]
            self.logger.info(f"Registered services for broker: {broker_name} - {service_list}")

    def get_service_class(self, broker_name: str, service_type: ServiceType) -> Optional[Type]:
        """
        Get service class for a broker and service type.

        Args:
            broker_name: Name of the broker
            service_type: Type of service

        Returns:
            Service class if found, None otherwise
        """
        broker_services = self._service_classes.get(broker_name, {})
        return broker_services.get(service_type)

    def broker_supports_service(self, broker_name: str, service_type: ServiceType) -> bool:
        """
        Check if a broker supports a specific service type.

        Args:
            broker_name: Name of the broker
            service_type: Type of service

        Returns:
            True if broker supports the service, False otherwise
        """
        return service_type in self._broker_capabilities.get(broker_name, [])

    def get_broker_capabilities(self, broker_name: str) -> List[ServiceType]:
        """
        Get the list of service types supported by a broker.

        Args:
            broker_name: Name of the broker

        Returns:
            List of supported service types
        """
        return self._broker_capabilities.get(broker_name, []).copy()

    def register_complete_broker(self, broker_name: str, config_class: Type[BaseConfig], **services) -> None:
        """
        Register both configuration and services for a broker in a single operation.

        Args:
            broker_name: Name of the broker
            config_class: Configuration class for the broker
            **services: Service classes keyed by service type name

        Raises:
            BrokerRegistryValidationError: If validation fails
        """
        with self._lock:
            try:
                self.register_broker_config(broker_name, config_class)
                self.register_broker_services(broker_name, **services)
            except Exception:
                # Rollback configuration registration if service registration fails
                if broker_name in self._config_classes:
                    del self._config_classes[broker_name]
                    self.logger.warning(f"Rolled back configuration registration for broker: {broker_name}")
                raise

    def get_registered_brokers(self) -> List[str]:
        """
        Get list of all registered broker names.

        Returns:
            List of broker names that have configurations registered
        """
        return list(self._config_classes.keys())

    def get_fully_registered_brokers(self) -> List[str]:
        """
        Get list of brokers that have both configuration and services registered.

        Returns:
            List of broker names that have both configuration and services
        """
        config_brokers = set(self._config_classes.keys())
        service_brokers = set(self._service_classes.keys())
        return list(config_brokers.intersection(service_brokers))

    def get_registration_status(self) -> Dict[str, Dict[str, bool]]:
        """
        Get registration status for all brokers.

        Returns:
            Dictionary mapping broker names to their registration status
        """
        all_brokers = set(self._config_classes.keys()) | set(self._service_classes.keys())
        return {
            broker_name: {
                "config_registered": broker_name in self._config_classes,
                "services_registered": broker_name in self._service_classes,
            }
            for broker_name in all_brokers
        }

    def validate_all_registrations(self) -> Dict[str, Any]:
        """
        Validate all broker registrations and return detailed status.

        Returns:
            Dictionary with validation results
        """
        results = {"all_valid": True, "brokers": {}}

        for broker_name in self.get_registered_brokers():
            broker_result = {"valid": True, "issues": []}

            # Check if broker has services registered
            if broker_name not in self._service_classes:
                broker_result["valid"] = False
                broker_result["issues"].append("No services registered")

            # Check if broker has required services
            elif ServiceType.PORTFOLIO not in self._broker_capabilities.get(broker_name, []):
                broker_result["valid"] = False
                broker_result["issues"].append("Missing required portfolio service")

            results["brokers"][broker_name] = broker_result
            if not broker_result["valid"]:
                results["all_valid"] = False

        return results

    def unregister_broker(self, broker_name: str) -> bool:
        """
        Unregister a broker and all its services.

        Args:
            broker_name: Name of the broker to unregister

        Returns:
            True if broker was unregistered, False if not found
        """
        with self._lock:
            found = False
            if broker_name in self._config_classes:
                del self._config_classes[broker_name]
                found = True
            if broker_name in self._service_classes:
                del self._service_classes[broker_name]
                found = True
            if broker_name in self._broker_capabilities:
                del self._broker_capabilities[broker_name]

            if found:
                self.logger.info(f"Unregistered broker: {broker_name}")

            return found

    def clear_all_registrations(self) -> None:
        """Clear all broker registrations."""
        with self._lock:
            self._config_classes.clear()
            self._service_classes.clear()
            self._broker_capabilities.clear()
            self.logger.info("Cleared all broker registrations")

    def validate_broker_service_compatibility(self, broker_name: str) -> Dict[str, Any]:
        """
        Validate that a broker's services are compatible with its configuration.

        Args:
            broker_name: Name of the broker to validate

        Returns:
            Dictionary with validation results including any issues found
        """
        result = {"valid": True, "issues": []}

        if not self.is_config_registered(broker_name):
            result["valid"] = False
            result["issues"].append("No configuration registered")
            return result

        if broker_name not in self._service_classes:
            result["valid"] = False
            result["issues"].append("No services registered")
            return result

        # Check for required services
        capabilities = self.get_broker_capabilities(broker_name)
        if ServiceType.PORTFOLIO not in capabilities:
            result["valid"] = False
            result["issues"].append("Missing required portfolio service")

        return result

    def _validate_broker_name(self, broker_name: str) -> None:
        """Validate broker name."""
        if not broker_name or not isinstance(broker_name, str):
            raise BrokerRegistryValidationError("Broker name must be a non-empty string")

        if not broker_name.isalnum():
            raise BrokerRegistryValidationError("Broker name must contain only alphanumeric characters")

    def _validate_config_class(self, config_class: Type[BaseConfig]) -> None:
        """Validate configuration class."""
        if not isinstance(config_class, type):
            raise BrokerRegistryValidationError("config_class must be a class type")

        if not issubclass(config_class, BaseConfig):
            raise BrokerRegistryValidationError("config_class must be a subclass of BaseConfig")

    def _validate_service_type(self, service_name: str) -> ServiceType:
        """Validate and convert service name to ServiceType."""
        try:
            return ServiceType(service_name)
        except ValueError:
            valid_types = [t.value for t in ServiceType]
            raise BrokerRegistryValidationError(
                f"Invalid service type '{service_name}'. Valid types: {valid_types}"
            ) from None

    def _validate_service_class(self, service_class: Type) -> None:
        """Validate service class."""
        if not isinstance(service_class, type):
            raise BrokerRegistryValidationError(
                f"Service '{service_class}' must be a class type, got {type(service_class)}"
            )
