# Unified Broker Architecture Strategy

## Current State Analysis

After reviewing both the configuration module and services/brokers module, I identified **two parallel but inconsistent patterns** for managing broker components.

### **Configuration Module Pattern**
```python
# 1. Registry (ConfigRegistry) - Instance-based
class ConfigRegistry:
    def __init__(self):
        self._broker_configs: Dict[str, BaseConfig] = {}
        self._broker_config_classes: Dict[str, Type[BaseConfig]] = {}

# 2. Factory (ConfigFactory) - Singleton
@singleton
class ConfigFactory:
    def __init__(self):
        self._config_classes: Dict[str, Type[BaseConfig]] = {}
        self._register_default_brokers()  # Auto-registration

# 3. Main Config class uses registry internally
class Config:
    def __init__(self):
        self.registry = ConfigRegistry()  # Instance-based
```

### **Services/Brokers Module Pattern**
```python
# 1. Registry (BrokerRegistry) - Singleton
@singleton
class BrokerRegistry:
    def __init__(self):
        self._brokers: Dict[str, Dict[str, Type]] = {}
        self._broker_capabilities: Dict[str, List[ServiceType]] = {}

# 2. Factory (ServiceFactory) - Singleton
@singleton
class ServiceFactory:
    def __init__(self):
        self._registry = BrokerRegistry()  # Uses singleton registry
        self._service_instances: Dict[str, Dict[str, Any]] = {}

# 3. Manual registration in registry_setup.py
def register_broker_services():
    registry = BrokerRegistry()
    registry.register_broker("degiro", ...)
    registry.register_broker("bitvavo", ...)
```

## **Inconsistencies Identified**

### 1. **Registry Pattern Inconsistency**
- **Config**: Uses instance-based `ConfigRegistry` (each `Config` has its own registry)
- **Services**: Uses singleton `BrokerRegistry` (global shared registry)

### 2. **Registration Strategy Inconsistency**
- **Config**: Auto-registration in factory constructor (`_register_default_brokers()`)
- **Services**: Manual registration in separate setup function (`register_broker_services()`)

### 3. **Factory Responsibilities Inconsistency**
- **Config**: Factory handles both registration AND creation
- **Services**: Factory only handles creation, registry handles registration

### 4. **Singleton Usage Inconsistency**
- **Config**: Factory is singleton, registry is instance-based
- **Services**: Both registry and factory are singletons

## **Recommended Unified Approach**

For better consistency, I recommend **standardizing on the Services pattern** because:

### **Why Services Pattern is Better:**

1. **Clear Separation of Concerns**:
   - Registry: Manages registration and capabilities
   - Factory: Handles instantiation and caching
   - Setup: Explicit registration control

2. **Better Testability**:
   - Singleton registries can be reset between tests
   - Explicit registration makes dependencies clear

3. **More Flexible**:
   - Can register services conditionally
   - Can unregister/re-register during runtime
   - Better for plugin architectures

## **Proposed Unified Pattern**

### **1. Unified Registry (Singleton)**
```python
@singleton
class BrokerRegistry:
    """
    Unified registry for managing both broker configurations and services.
    """
    def __init__(self):
        # Configuration management
        self._config_classes: Dict[str, Type[BaseConfig]] = {}
        self._config_instances: Dict[str, BaseConfig] = {}

        # Service management
        self._service_classes: Dict[str, Dict[str, Type]] = {}
        self._broker_capabilities: Dict[str, List[ServiceType]] = {}

    # Configuration methods
    def register_config(self, broker_name: str, config_class: Type[BaseConfig]) -> None:
        """Register a broker configuration class."""
        self._config_classes[broker_name] = config_class

    def get_config_class(self, broker_name: str) -> Optional[Type[BaseConfig]]:
        """Get configuration class for a broker."""
        return self._config_classes.get(broker_name)

    # Service methods (existing)
    def register_broker(self, broker_name: str, **services) -> None:
        """Register broker services."""
        # Existing implementation

    def get_broker_service(self, broker_name: str, service_type: ServiceType) -> Optional[Type]:
        """Get service class for a broker."""
        # Existing implementation
```

### **2. Unified Factory (Singleton)**
```python
@singleton
class BrokerFactory:
    """
    Unified factory for creating both broker configurations and services.
    """
    def __init__(self):
        self._registry = BrokerRegistry()
        self._config_instances: Dict[str, BaseConfig] = {}
        self._service_instances: Dict[str, Dict[str, Any]] = {}

    # Configuration creation methods
    def create_config(self, broker_name: str, **kwargs) -> Optional[BaseConfig]:
        """Create a broker configuration instance."""
        config_class = self._registry.get_config_class(broker_name)
        if not config_class:
            return None

        cache_key = f"config_{broker_name}"
        if cache_key not in self._config_instances:
            self._config_instances[cache_key] = config_class(**kwargs)

        return self._config_instances[cache_key]

    def create_default_config(self, broker_name: str) -> Optional[BaseConfig]:
        """Create a default broker configuration."""
        config_class = self._registry.get_config_class(broker_name)
        if not config_class:
            return None

        return config_class.default()

    # Service creation methods (existing)
    def create_portfolio_service(self, broker_name: str, **kwargs) -> PortfolioServiceInterface:
        """Create a portfolio service instance."""
        # Existing implementation

    def create_transaction_service(self, broker_name: str, **kwargs) -> TransactionServiceInterface:
        """Create a transaction service instance."""
        # Existing implementation
```

### **3. Unified Setup**
```python
def register_all_brokers() -> None:
    """
    Register all broker configurations and services.
    This should be called during application initialization.
    """
    registry = BrokerRegistry()

    # Register configurations
    registry.register_config("degiro", DegiroConfig)
    registry.register_config("bitvavo", BitvavoConfig)

    # Register services
    registry.register_broker(
        broker_name="degiro",
        portfolio_service=DeGiroPortfolioService,
        transaction_service=DeGiroTransactionService,
        deposit_service=DeGiroDepositService,
        dividend_service=DeGiroDividendService,
        fee_service=DeGiroFeeService,
        account_service=DeGiroAccountService,
    )

    registry.register_broker(
        broker_name="bitvavo",
        portfolio_service=BitvavoPortfolioService,
        transaction_service=BitvavoTransactionService,
        deposit_service=BitvavoDepositService,
        dividend_service=None,  # Bitvavo doesn't support dividends
        fee_service=BitvavoFeeService,
        account_service=BitvavoAccountService,
    )
```

### **4. Updated Config Class**
```python
class Config:
    """
    Main configuration class using unified registry/factory.
    """
    def __init__(self, base_currency: str = "EUR"):
        self.base_currency = base_currency
        self._factory = BrokerFactory()
        self._registry = BrokerRegistry()

    def get_broker_config(self, broker_name: str) -> Optional[BaseConfig]:
        """Get broker configuration using unified factory."""
        return self._factory.create_default_config(broker_name)

    def is_broker_enabled(self, broker_name: str) -> bool:
        """Check if broker is enabled using unified registry."""
        config = self.get_broker_config(broker_name)
        return config.is_enabled() if config else False

    @classmethod
    def default(cls) -> "Config":
        """Create default configuration using unified factory."""
        config = cls()
        # Factory handles all broker config creation
        return config
```

## **Migration Strategy**

### **Phase 1: Create Unified Registry**
- [ ] Create new `BrokerRegistry` that handles both configs and services
- [ ] Add configuration management methods to existing `BrokerRegistry`
- [ ] Update tests to use unified registry

### **Phase 2: Create Unified Factory**
- [ ] Create new `BrokerFactory` that handles both config and service creation
- [ ] Add configuration creation methods to factory
- [ ] Implement caching for both configs and services

### **Phase 3: Update Config Class**
- [ ] Modify `Config` class to use unified registry/factory
- [ ] Remove instance-based `ConfigRegistry`
- [ ] Update all config-related tests

### **Phase 4: Cleanup**
- [ ] Remove old `ConfigFactory` and `ConfigRegistry`
- [ ] Remove old `ServiceFactory` (if not already unified)
- [ ] Update all imports and references
- [ ] Update documentation

## **Benefits of Unified Approach**

1. **Single Source of Truth**: One registry for all broker components
2. **Consistent Patterns**: Same registration/creation patterns everywhere
3. **Better Extensibility**: Adding new brokers requires changes in one place
4. **Simpler Testing**: Unified setup/teardown for all broker components
5. **Reduced Code Duplication**: Shared logic for registration and creation
6. **Better Maintainability**: Less code to maintain and understand

## **Backward Compatibility**

The migration should maintain backward compatibility:
- Existing `Config.default()` calls should continue to work
- Existing service factory calls should continue to work
- Gradual migration allows for testing at each phase

## **Testing Strategy**

1. **Unit Tests**: Test each component in isolation
2. **Integration Tests**: Test the unified registry/factory together
3. **Migration Tests**: Ensure existing functionality continues to work
4. **Performance Tests**: Ensure no performance regression

---

*This document should be updated as the migration progresses and any issues or improvements are discovered.*
