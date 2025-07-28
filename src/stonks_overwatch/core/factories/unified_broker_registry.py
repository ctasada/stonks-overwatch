"""
Unified broker registry for managing both configurations and services.

This module provides a unified registry that handles both broker configurations
and services in a single, consistent interface, eliminating the need for
separate registry systems.
"""

from typing import Any, Dict, List, Optional, Set, Type

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.core.exceptions import ServiceRegistryException
from stonks_overwatch.core.service_types import ServiceType
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.core.singleton import singleton


class BrokerRegistryValidationError(ServiceRegistryException):
    """Exception raised for broker registry validation errors."""

    pass


@singleton
class UnifiedBrokerRegistry:
    """
    Unified registry for managing both broker configurations and services.

    This singleton class provides a centralized way to register and manage
    both broker configurations and their associated services, ensuring
    consistency and eliminating the need for separate registry systems.
    """

    def __init__(self):
        """
        Initialize the unified broker registry.

        Sets up empty dictionaries for managing broker configurations and services,
        and initializes logging for registry operations.
        """
        self.logger = StonksLogger.get_logger("stonks_overwatch.core", "[UNIFIED_REGISTRY]")

        # Configuration management
        self._config_classes: Dict[str, Type[BaseConfig]] = {}

        # Service management
        self._service_classes: Dict[str, Dict[ServiceType, Type]] = {}
        self._broker_capabilities: Dict[str, List[ServiceType]] = {}

        # Internal state for validation
        self._initialized_brokers: Set[str] = set()

    # Configuration methods
    def register_broker_config(self, broker_name: str, config_class: Type[BaseConfig]) -> None:
        """
        Register a broker configuration class.

        Args:
            broker_name: Name of the broker (e.g., 'degiro', 'bitvavo')
            config_class: Configuration class for the broker

        Raises:
            BrokerRegistryValidationError: If validation fails
        """
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
            Configuration class if registered, None otherwise
        """
        return self._config_classes.get(broker_name)

    def is_config_registered(self, broker_name: str) -> bool:
        """
        Check if a configuration is registered for a broker.

        Args:
            broker_name: Name of the broker

        Returns:
            True if configuration is registered, False otherwise
        """
        return broker_name in self._config_classes

    def get_registered_config_brokers(self) -> List[str]:
        """
        Get list of all brokers with registered configurations.

        Returns:
            List of broker names with configurations
        """
        return list(self._config_classes.keys())

    # Service methods
    def register_broker_services(self, broker_name: str, **services) -> None:
        """
        Register broker service classes.

        Args:
            broker_name: Name of the broker
            **services: Service classes mapped by ServiceType

        Raises:
            BrokerRegistryValidationError: If validation fails
        """
        self._validate_broker_name(broker_name)
        self._validate_services(services)

        if broker_name in self._service_classes:
            raise BrokerRegistryValidationError(f"Services for broker '{broker_name}' are already registered")

        # Convert string keys to ServiceType enum
        service_map = {}
        capabilities = []

        for service_name, service_class in services.items():
            try:
                service_type = ServiceType(service_name.lower())
                service_map[service_type] = service_class
                capabilities.append(service_type)
            except ValueError as err:
                raise BrokerRegistryValidationError(
                    f"Unknown service type '{service_name}' for broker '{broker_name}'. "
                    f"Valid types: {[st.value for st in ServiceType]}"
                ) from err

        # Validate required services
        self._validate_required_services(broker_name, capabilities)

        self._service_classes[broker_name] = service_map
        self._broker_capabilities[broker_name] = capabilities
        self.logger.info(f"Registered services for broker: {broker_name} - {[s.value for s in capabilities]}")

    def get_service_class(self, broker_name: str, service_type: ServiceType) -> Optional[Type]:
        """
        Get service class for a broker and service type.

        Args:
            broker_name: Name of the broker
            service_type: Type of service to retrieve

        Returns:
            Service class if available, None otherwise
        """
        return self._service_classes.get(broker_name, {}).get(service_type)

    def is_service_registered(self, broker_name: str) -> bool:
        """
        Check if services are registered for a broker.

        Args:
            broker_name: Name of the broker

        Returns:
            True if services are registered, False otherwise
        """
        return broker_name in self._service_classes

    def get_registered_service_brokers(self) -> List[str]:
        """
        Get list of all brokers with registered services.

        Returns:
            List of broker names with services
        """
        return list(self._service_classes.keys())

    def get_broker_capabilities(self, broker_name: str) -> List[ServiceType]:
        """
        Get the capabilities (service types) of a specific broker.

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

    # Unified methods
    def register_complete_broker(self, broker_name: str, config_class: Type[BaseConfig], **services) -> None:
        """
        Register both configuration and services for a broker in one call.

        Args:
            broker_name: Name of the broker
            config_class: Configuration class for the broker
            **services: Service classes mapped by ServiceType

        Raises:
            BrokerRegistryValidationError: If validation fails
        """
        # Register configuration first
        self.register_broker_config(broker_name, config_class)

        try:
            # Then register services
            self.register_broker_services(broker_name, **services)
            self._initialized_brokers.add(broker_name)
            self.logger.info(f"Completely registered broker: {broker_name}")
        except Exception:
            # If service registration fails, rollback config registration
            self._config_classes.pop(broker_name, None)
            raise

    def get_fully_registered_brokers(self) -> List[str]:
        """
        Get all brokers that have both configuration and service registrations.

        Returns:
            List of broker names with both config and services
        """
        config_brokers = set(self._config_classes.keys())
        service_brokers = set(self._service_classes.keys())
        return sorted(config_brokers.intersection(service_brokers))

    def is_fully_registered(self, broker_name: str) -> bool:
        """
        Check if a broker has both configuration and service registrations.

        Args:
            broker_name: Name of the broker

        Returns:
            True if both config and services are registered, False otherwise
        """
        return self.is_config_registered(broker_name) and self.is_service_registered(broker_name)

    def get_registration_status(self, broker_name: str) -> Dict[str, bool]:
        """
        Get the registration status for a broker.

        Args:
            broker_name: Name of the broker

        Returns:
            Dictionary with config and service registration status
        """
        return {
            "config_registered": self.is_config_registered(broker_name),
            "services_registered": self.is_service_registered(broker_name),
            "fully_registered": self.is_fully_registered(broker_name),
        }

    def validate_all_registrations(self) -> Dict[str, List[str]]:
        """
        Validate all broker registrations and return any issues found.

        Returns:
            Dictionary with validation issues by category
        """
        issues = {"missing_configs": [], "missing_services": [], "incomplete_registrations": []}

        all_brokers = set(self._config_classes.keys()) | set(self._service_classes.keys())

        for broker_name in all_brokers:
            if not self.is_config_registered(broker_name):
                issues["missing_configs"].append(broker_name)
            if not self.is_service_registered(broker_name):
                issues["missing_services"].append(broker_name)
            if not self.is_fully_registered(broker_name):
                issues["incomplete_registrations"].append(broker_name)

        return issues

    def validate_broker_service_compatibility(self, broker_name: str) -> Dict[str, Any]:
        """
        Validate that a broker's services are compatible with its configuration.

        Args:
            broker_name: Name of the broker to validate

        Returns:
            Dictionary with validation results including any issues found
        """
        validation_result = {
            "broker_name": broker_name,
            "is_valid": True,
            "issues": [],
            "config_class": None,
            "service_types": [],
        }

        # Check if broker is registered
        if broker_name not in self._config_classes:
            validation_result["is_valid"] = False
            validation_result["issues"].append(f"No configuration class registered for {broker_name}")
            return validation_result

        if broker_name not in self._service_classes:
            validation_result["is_valid"] = False
            validation_result["issues"].append(f"No services registered for {broker_name}")
            return validation_result

        validation_result["config_class"] = self._config_classes[broker_name].__name__
        validation_result["service_types"] = list(self._service_classes[broker_name].keys())

        # Validate required services are present
        required_services = {ServiceType.PORTFOLIO}  # Portfolio is always required
        registered_services = set(self._service_classes[broker_name].keys())

        missing_required = required_services - registered_services
        if missing_required:
            validation_result["is_valid"] = False
            validation_result["issues"].append(f"Missing required services: {missing_required}")

        self.logger.debug(f"Validated {broker_name}: {validation_result}")
        return validation_result

    # Cleanup methods
    def unregister_broker(self, broker_name: str) -> None:
        """
        Unregister both configuration and services for a broker.

        Args:
            broker_name: Name of the broker to unregister
        """
        removed_items = []

        if broker_name in self._config_classes:
            del self._config_classes[broker_name]
            removed_items.append("config")

        if broker_name in self._service_classes:
            del self._service_classes[broker_name]
            removed_items.append("services")

        if broker_name in self._broker_capabilities:
            del self._broker_capabilities[broker_name]

        self._initialized_brokers.discard(broker_name)

        if removed_items:
            self.logger.info(f"Unregistered {', '.join(removed_items)} for broker: {broker_name}")

    def clear_all_registrations(self) -> None:
        """Clear all broker registrations."""
        self._config_classes.clear()
        self._service_classes.clear()
        self._broker_capabilities.clear()
        self._initialized_brokers.clear()
        self.logger.info("Cleared all broker registrations")

    # Validation methods
    def _validate_broker_name(self, broker_name: str) -> None:
        """Validate broker name format."""
        if not broker_name:
            raise BrokerRegistryValidationError("Broker name cannot be empty")

        if not isinstance(broker_name, str):
            raise BrokerRegistryValidationError("Broker name must be a string")

        if not broker_name.islower():
            raise BrokerRegistryValidationError(f"Broker name '{broker_name}' must be lowercase")

        if not broker_name.replace("_", "").isalnum():
            raise BrokerRegistryValidationError(
                f"Broker name '{broker_name}' must contain only alphanumeric characters and underscores"
            )

    def _validate_config_class(self, config_class: Type[BaseConfig]) -> None:
        """Validate configuration class."""
        if not isinstance(config_class, type):
            raise BrokerRegistryValidationError("config_class must be a class type")

        if not issubclass(config_class, BaseConfig):
            raise BrokerRegistryValidationError(
                f"Configuration class {config_class.__name__} must inherit from BaseConfig"
            )

    def _validate_services(self, services: Dict[str, Type]) -> None:
        """Validate service classes."""
        if not services:
            raise BrokerRegistryValidationError("At least one service must be provided")

        for service_name, service_class in services.items():
            if not isinstance(service_class, type):
                raise BrokerRegistryValidationError(
                    f"Service '{service_name}' must be a class type, got {type(service_class)}"
                )

    def _validate_required_services(self, broker_name: str, capabilities: List[ServiceType]) -> None:
        """
        Validate that minimum required services are provided.

        Note: Only portfolio service is truly required. Other services (transaction, deposit, etc.)
        are optional and depend on what the broker actually supports.
        """
        required_services = {ServiceType.PORTFOLIO}  # Only portfolio is truly required
        provided_services = set(capabilities)

        missing_services = required_services - provided_services
        if missing_services:
            missing_names = [service.value for service in missing_services]
            raise BrokerRegistryValidationError(f"Broker '{broker_name}' is missing required services: {missing_names}")

        # Log what services are actually provided for debugging
        self.logger.debug(f"Broker '{broker_name}' registered with services: {[s.value for s in capabilities]}")
