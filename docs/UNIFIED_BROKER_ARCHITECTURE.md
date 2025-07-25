# Unified Broker Architecture Strategy

## Executive Summary

After conducting a comprehensive review of the codebase, I've identified significant architectural inconsistencies between the configuration and services modules that manage broker components. This document provides an analysis of the current state, identifies key issues, and proposes a unified architecture with concrete implementation tasks.

## Current State Analysis

The system currently uses **two different architectural patterns** for managing broker components, leading to inconsistencies and maintenance complexity.

### **Configuration Module Architecture**

Located in `src/stonks_overwatch/config/`:

```python
# 1. ConfigFactory (Singleton) - Auto-registration
@singleton
class ConfigFactory:
    def __init__(self):
        self._config_classes: Dict[str, Type[BaseConfig]] = {}
        self._register_default_brokers()  # Auto-registers degiro, bitvavo, ibkr

# 2. ConfigRegistry (Instance-based) - Per-Config instance
class ConfigRegistry:
    def __init__(self):
        self._broker_configs: Dict[str, BaseConfig] = {}
        self._broker_config_classes: Dict[str, Type[BaseConfig]] = {}

# 3. Config Class - Uses instance-based registry
class Config:
    def __init__(self):
        self.registry = ConfigRegistry()  # Each Config has its own registry
```

**Access Pattern:**

```python
# Services access config via global singleton
config = Config.get_global().registry.get_broker_config("degiro")
```

### **Services Module Architecture**

Located in `src/stonks_overwatch/core/factories/` and `src/stonks_overwatch/services/`:

```python
# 1. BrokerRegistry (Singleton) - Global shared registry
@singleton
class BrokerRegistry:
    def __init__(self):
        self._brokers: Dict[str, Dict[str, Type]] = {}
        self._broker_capabilities: Dict[str, List[ServiceType]] = {}

# 2. ServiceFactory (Singleton) - Uses singleton registry
@singleton
class ServiceFactory:
    def __init__(self):
        self._registry = BrokerRegistry()
        self._service_instances: Dict[str, Dict[str, Any]] = {}

# 3. Manual Registration - Called during app startup
def register_broker_services():
    registry = BrokerRegistry()
    registry.register_broker("degiro", portfolio_service=..., transaction_service=...)
```

**Access Pattern:**

```python
# Aggregators bypass factory and create services manually
if broker_name == "degiro":
    return self._create_degiro_service()  # Hardcoded creation
```

## Critical Issues Identified

### 1. **Architectural Inconsistency**

- **Config**: Instance-based registry (each Config has separate registry)
- **Services**: Singleton registry (global shared registry)
- **Result**: Different patterns for the same conceptual domain

### 2. **Registration Strategy Inconsistency**

- **Config**: Auto-registration in factory constructor
- **Services**: Manual registration in separate setup function
- **Result**: Different broker registration workflows

### 3. **Tight Coupling Between Layers**

- Services directly access global config: `Config.get_global().registry.get_broker_config()`
- No dependency injection between config and services
- **Result**: Difficult to test and modify

### 4. **Factory Pattern Bypassing**

- `BaseAggregator` manually creates services instead of using `ServiceFactory`
- Hardcoded service creation with manual dependency resolution
- **Result**: Factory pattern benefits lost

### 5. **Singleton Usage Inconsistency**

- **Config**: Factory is singleton, registry is instance-based
- **Services**: Both registry and factory are singletons
- **Result**: Confusing memory management and initialization

### 6. **No Unified Broker Management**

- Brokers must be registered in two separate systems
- No guarantee that config and service registrations stay in sync
- **Result**: Potential runtime errors from mismatched registrations

### 7. **🚨 CRITICAL: Extremely High File Modification Burden**

Adding a new broker requires modifying **8-10+ files** across the entire codebase:

#### **Configuration Layer Changes (4-5 files):**

```bash
# 1. Create new broker config file
touch src/stonks_overwatch/config/new_broker.py

# 2. Modify config_factory.py - Add import + registration
# File: src/stonks_overwatch/config/config_factory.py
from stonks_overwatch.config.new_broker import NewBrokerConfig  # ADD THIS

def _register_default_brokers(self) -> None:
    self.register_broker_config("degiro", DegiroConfig)
    self.register_broker_config("bitvavo", BitvavoConfig)
    self.register_broker_config("ibkr", IbkrConfig)
    self.register_broker_config("new_broker", NewBrokerConfig)  # ADD THIS

# 3. Modify config.py - Add import + constructor + from_dict method
# File: src/stonks_overwatch/config/config.py
from stonks_overwatch.config.new_broker import NewBrokerConfig  # ADD THIS

def __init__(
    self,
    base_currency: Optional[str] = DEFAULT_BASE_CURRENCY,
    degiro_configuration: Optional[DegiroConfig] = None,
    bitvavo_configuration: Optional[BitvavoConfig] = None,
    ibkr_configuration: Optional[IbkrConfig] = None,
    new_broker_configuration: Optional[NewBrokerConfig] = None,  # ADD THIS
) -> None:
    # ... existing code ...
    if new_broker_configuration:  # ADD THIS
        self.registry.set_broker_config("new_broker", new_broker_configuration)

# 4. Update from_dict method in config.py
@classmethod
def from_dict(cls, data: dict) -> "Config":
    new_broker_configuration = config_factory.create_broker_config_from_dict(
        "new_broker", data.get(NewBrokerConfig.config_key, {})  # ADD THIS
    )
```

#### **Services Layer Changes (3-4 files):**

```bash
# 5. Create entire broker service directory structure
mkdir -p src/stonks_overwatch/services/brokers/new_broker/{client,services,repositories}
# ... create multiple service files

# 6. Modify registry_setup.py - Add multiple imports + registration
# File: src/stonks_overwatch/core/registry_setup.py
from stonks_overwatch.services.brokers.new_broker.services.account_service import (
    AccountOverviewService as NewBrokerAccountService,  # ADD THIS
)
from stonks_overwatch.services.brokers.new_broker.services.portfolio_service import (
    PortfolioService as NewBrokerPortfolioService,  # ADD THIS
)
# ... ADD 4-6 MORE IMPORTS

def register_broker_services() -> None:
    registry.register_broker(
        broker_name="new_broker",  # ADD ENTIRE REGISTRATION BLOCK
        portfolio_service=NewBrokerPortfolioService,
        transaction_service=NewBrokerTransactionService,
        deposit_service=NewBrokerDepositService,
        # ... more services
    )

# 7. Modify base_aggregator.py - Add hardcoded service creation method
# File: src/stonks_overwatch/core/aggregators/base_aggregator.py
def _get_broker_service(self, broker_name: str) -> Optional[Any]:
    if broker_name == "degiro":
        return self._create_degiro_service()
    elif broker_name == "bitvavo":
        return self._create_bitvavo_service()
    elif broker_name == "ibkr":
        return self._create_ibkr_service()
    elif broker_name == "new_broker":  # ADD THIS
        return self._create_new_broker_service()  # ADD THIS

def _create_new_broker_service(self) -> Optional[Any]:  # ADD ENTIRE METHOD
    """Create NewBroker service with proper dependencies."""
    # ... complex hardcoded service creation logic

def _is_broker_enabled(self, broker_name: str, selected_portfolio: PortfolioId) -> bool:
    if broker_name == "degiro":
        return self._config.is_degiro_enabled(selected_portfolio)
    elif broker_name == "bitvavo":
        return self._config.is_bitvavo_enabled(selected_portfolio)
    elif broker_name == "ibkr":
        return self._config.is_ibkr_enabled(selected_portfolio)
    elif broker_name == "new_broker":  # ADD THIS
        return self._config.is_new_broker_enabled(selected_portfolio)  # ADD THIS
```

### 8. **🚨 CRITICAL: Widespread Hardcoded Broker Logic**

The codebase is **littered with hardcoded broker names** that must be manually updated:

```python
# Found in multiple files - config.py, base_aggregator.py, etc.
if broker_name == "bitvavo":
    return config.is_enabled() and config is not None and config.credentials is not None
elif broker_name == "degiro":
    return self._is_degiro_connected(selected_portfolio)
elif broker_name == "ibkr":
    return self._is_ibkr_connected(selected_portfolio)
# MUST ADD: elif broker_name == "new_broker": ...

# Found in base_aggregator.py
if broker_name == "degiro":
    return self._create_degiro_service()
elif broker_name == "bitvavo":
    return self._create_bitvavo_service()
elif broker_name == "ibkr":
    return self._create_ibkr_service()
# MUST ADD: elif broker_name == "new_broker": ...
```

### 9. **🚨 CRITICAL: No Compile-Time Safety**

- **Missing broker registration**: No warning if you forget to register in one system but not the other
- **Typos in broker names**: String-based broker identification prone to typos
- **Missing hardcoded cases**: Easy to forget adding `elif broker_name == "new_broker"` checks
- **Import errors**: No validation that all required imports are added

### 10. **🚨 CRITICAL: Documentation Drift**

- **Outdated guides**: Broker integration guides become stale as more places need modification
- **Hidden dependencies**: No clear documentation of ALL files that need changes
- **Manual process**: Entirely manual process with no automation or validation

### 11. **🚨 CRITICAL: Testing Complexity**

- **Scattered test updates**: Tests must be updated in multiple modules
- **Mock proliferation**: Each layer needs separate mocking strategies
- **Integration test gaps**: Easy to miss testing the integration between config and services

## Error-Prone New Broker Addition Analysis

Based on the README and actual code analysis, adding a new broker requires:

### **Minimum Required Steps (8-10 files modified):**

1. ✅ Create `src/stonks_overwatch/config/new_broker.py`
2. ❌ Modify `src/stonks_overwatch/config/config_factory.py` (import + registration)
3. ❌ Modify `src/stonks_overwatch/config/config.py` (import + constructor + from_dict)
4. ✅ Create `src/stonks_overwatch/services/brokers/new_broker/` structure
5. ❌ Modify `src/stonks_overwatch/core/registry_setup.py` (imports + registration)
6. ❌ Modify `src/stonks_overwatch/core/aggregators/base_aggregator.py` (service creation + enabled checks)
7. ❌ Update any scripts/utilities that reference broker names
8. ❌ Update hardcoded broker checks throughout codebase

### **Failure Points:**

- ❌ **Forgotten import**: Easy to forget importing config class in multiple files
- ❌ **Missed registration**: Easy to register config but forget services (or vice versa)
- ❌ **Incomplete hardcoded logic**: Easy to miss adding broker-specific `elif` branches
- ❌ **Constructor signature**: Must remember to add constructor parameter to `Config` class
- ❌ **from_dict method**: Must remember to add broker to dictionary parsing logic
- ❌ **Testing gaps**: Must remember to update tests in multiple modules

### **Real-World Consequences:**

- 🔥 **Runtime errors**: Missing registration causes `None` returns and crashes
- 🔥 **Silent failures**: Broker appears "available" but services don't work
- 🔥 **Configuration drift**: Config exists but services don't (or vice versa)
- 🔥 **Maintenance burden**: Future developers must understand the entire scattered system

## Recommended Unified Architecture

### **Core Principle: Single Responsibility with Unified Management**

Create a unified broker management system that handles both configurations and services consistently, while maintaining clear separation of concerns.

### **1. Unified Registry Pattern (Singleton)**

```python
@singleton
class UnifiedBrokerRegistry:
    """
    Single registry for managing all broker components (configs + services).
    """
    def __init__(self):
        # Configuration management
        self._config_classes: Dict[str, Type[BaseConfig]] = {}

        # Service management
        self._service_classes: Dict[str, Dict[ServiceType, Type]] = {}
        self._broker_capabilities: Dict[str, List[ServiceType]] = {}

    # Configuration methods
    def register_broker_config(self, broker_name: str, config_class: Type[BaseConfig]) -> None:
        """Register a broker configuration class."""
        self._config_classes[broker_name] = config_class

    def get_config_class(self, broker_name: str) -> Optional[Type[BaseConfig]]:
        """Get configuration class for a broker."""
        return self._config_classes.get(broker_name)

    # Service methods
    def register_broker_services(self, broker_name: str, **services) -> None:
        """Register broker service classes."""
        self._service_classes[broker_name] = services
        self._broker_capabilities[broker_name] = list(services.keys())

    def get_service_class(self, broker_name: str, service_type: ServiceType) -> Optional[Type]:
        """Get service class for a broker."""
        return self._service_classes.get(broker_name, {}).get(service_type)

    # Unified methods
    def get_registered_brokers(self) -> List[str]:
        """Get all brokers that have both config and service registrations."""
        config_brokers = set(self._config_classes.keys())
        service_brokers = set(self._service_classes.keys())
        return list(config_brokers.intersection(service_brokers))
```

### **2. Unified Factory Pattern (Singleton)**

```python
@singleton
class UnifiedBrokerFactory:
    """
    Single factory for creating both configurations and services with dependency injection.
    """
    def __init__(self):
        self._registry = UnifiedBrokerRegistry()
        self._config_instances: Dict[str, BaseConfig] = {}
        self._service_instances: Dict[str, Dict[ServiceType, Any]] = {}

    # Configuration creation
    def create_config(self, broker_name: str, **kwargs) -> Optional[BaseConfig]:
        """Create broker configuration instance."""
        if broker_name in self._config_instances:
            return self._config_instances[broker_name]

        config_class = self._registry.get_config_class(broker_name)
        if config_class:
            config = config_class(**kwargs)
            self._config_instances[broker_name] = config
            return config
        return None

    # Service creation with dependency injection
    def create_service(self, broker_name: str, service_type: ServiceType, **kwargs) -> Optional[Any]:
        """Create service instance with automatic config injection."""
        cache_key = (broker_name, service_type)

        if cache_key in self._service_instances.get(broker_name, {}):
            return self._service_instances[broker_name][cache_key]

        service_class = self._registry.get_service_class(broker_name, service_type)
        if not service_class:
            return None

        # Automatic dependency injection
        config = self.create_config(broker_name)
        if config:
            kwargs['config'] = config

        # Create service instance
        service = service_class(**kwargs)

        # Cache it
        if broker_name not in self._service_instances:
            self._service_instances[broker_name] = {}
        self._service_instances[broker_name][cache_key] = service

        return service

    def get_available_brokers(self) -> List[str]:
        """Get brokers available for both config and services."""
        return self._registry.get_registered_brokers()
```

### **3. Simplified Configuration Class**

```python
class Config:
    """
    Main configuration class using unified registry/factory.
    """
    def __init__(self, base_currency: str = "EUR"):
        self.base_currency = base_currency
        self._factory = UnifiedBrokerFactory()

    def get_broker_config(self, broker_name: str) -> Optional[BaseConfig]:
        """Get broker configuration using unified factory."""
        return self._factory.create_config(broker_name)

    def is_broker_enabled(self, broker_name: str) -> bool:
        """Check if broker is enabled."""
        config = self.get_broker_config(broker_name)
        return config.is_enabled() if config else False

    @classmethod
    def get_global(cls) -> "Config":
        """Get global configuration instance."""
        # Use existing GlobalConfig pattern
        from stonks_overwatch.config.global_config import global_config
        return global_config.get_config()
```

### **4. Unified Registration Setup**

```python
def register_all_brokers() -> None:
    """
    Single function to register all broker configurations and services.
    Called during application initialization.
    """
    registry = UnifiedBrokerRegistry()

    # Register DeGiro
    registry.register_broker_config("degiro", DegiroConfig)
    registry.register_broker_services(
        "degiro",
        portfolio=DeGiroPortfolioService,
        transaction=DeGiroTransactionService,
        deposit=DeGiroDepositService,
        dividend=DeGiroDividendService,
        fee=DeGiroFeeService,
        account=DeGiroAccountService,
    )

    # Register Bitvavo
    registry.register_broker_config("bitvavo", BitvavoConfig)
    registry.register_broker_services(
        "bitvavo",
        portfolio=BitvavoPortfolioService,
        transaction=BitvavoTransactionService,
        deposit=BitvavoDepositService,
        fee=BitvavoFeeService,
        account=BitvavoAccountService,
    )

    # Register IBKR
    registry.register_broker_config("ibkr", IbkrConfig)
    registry.register_broker_services(
        "ibkr",
        portfolio=IbkrPortfolioService,
        transaction=IbkrTransactionService,
        dividend=IbkrDividendsService,
        account=IbkrAccountOverviewService,
    )

    # Adding new broker becomes a simple 2-step process:
    # registry.register_broker_config("new_broker", NewBrokerConfig)
    # registry.register_broker_services("new_broker", portfolio=..., transaction=...)
```

### **5. Updated Service Interface**

```python
# Updated base aggregator to use unified factory
class BaseAggregator(ABC):
    def __init__(self, service_type: ServiceType):
        self._service_type = service_type
        self._factory = UnifiedBrokerFactory()
        self._config = Config.get_global()

    def _get_broker_service(self, broker_name: str) -> Optional[Any]:
        """Get service using unified factory with dependency injection."""
        return self._factory.create_service(broker_name, self._service_type)

    def _is_broker_enabled(self, broker_name: str, selected_portfolio: PortfolioId) -> bool:
        """Check if broker is enabled - NO MORE HARDCODED CHECKS!"""
        config = self._factory.create_config(broker_name)
        if not config:
            return False
        return config.is_enabled()  # Unified interface
```

## New Broker Addition: Before vs After

### **❌ Current Process (8-10 files to modify):**

```bash
# 1. Create config file
# 2. Modify config_factory.py (import + registration)
# 3. Modify config.py (import + constructor + from_dict)
# 4. Create service directory structure
# 5. Modify registry_setup.py (imports + registration)
# 6. Modify base_aggregator.py (service creation + enabled checks)
# 7. Update hardcoded broker name checks throughout codebase
# 8. Update tests in multiple modules
# Risk: Miss any step = runtime failure
```

### **✅ Unified Process (2 files to modify):**

```bash
# 1. Create config file: src/stonks_overwatch/config/new_broker.py
# 2. Create service directory structure
# 3. Add 2 lines to registry_setup.py:
registry.register_broker_config("new_broker", NewBrokerConfig)
registry.register_broker_services("new_broker", portfolio=..., transaction=...)

# That's it! No hardcoded logic, no scattered changes, no missed steps.
```

## Implementation Strategy

### **Phase 1: Create Unified Registry (Week 1)** ✅ COMPLETED

#### Task 1.1: Create UnifiedBrokerRegistry ✅ COMPLETED

- [x] Create `core/factories/unified_broker_registry.py`
- [x] Implement configuration registration methods
- [x] Implement service registration methods
- [x] Add validation for consistent broker registrations
- [x] Write comprehensive unit tests

#### Task 1.2: Update Service Types Enum ✅ COMPLETED (No Changes Needed)

- [x] Extend `ServiceType` enum if needed ➜ **Analysis: Enum already complete**
- [x] Ensure all existing service types are covered ➜ **Verified: All 6 types covered**
- [x] Update type hints throughout codebase ➜ **Verified: Type hints already correct**

**Analysis Results:**
- Current `ServiceType` enum includes: PORTFOLIO, TRANSACTION, DEPOSIT, DIVIDEND, FEE, ACCOUNT
- All broker registrations use exactly these service types
- No additional service types found in codebase
- Conclusion: No updates needed - enum is complete

**Phase 1 Results:**
- ✅ Created `UnifiedBrokerRegistry` with 26 comprehensive tests
- ✅ All validation features implemented (broker names, config classes, required services)
- ✅ Rollback support and comprehensive error handling
- ✅ ServiceType enum verified complete - no updates needed
- ✅ 47/47 tests passing (26 new + 21 existing)

### **Phase 2: Create Unified Factory (Week 2)**

#### Task 2.1: Create UnifiedBrokerFactory ✅ COMPLETED

- [x] Create `core/factories/unified_broker_factory.py`
- [x] Implement configuration creation methods
- [x] Implement service creation with dependency injection
- [x] Add proper caching mechanisms
- [x] Write comprehensive unit tests

**Task 2.1 Results:**
- ✅ Created `UnifiedBrokerFactory` with 38 comprehensive tests
- ✅ Automatic dependency injection of configurations into services
- ✅ Full caching support for both configs and services
- ✅ Error handling and rollback support
- ✅ 85/85 tests passing (38 new + 47 existing)

#### Task 2.2: Update Service Interfaces ✅ COMPLETED

- [x] Modify service constructors to accept config parameter
- [x] Update service interfaces to be dependency-injection friendly
- [x] Ensure backward compatibility during transition

**Task 2.2 Results:**
- ✅ Created `BaseService` and `DependencyInjectionMixin` classes
- ✅ Updated all service interfaces with dependency injection documentation
- ✅ Automatic fallback to global config for backward compatibility
- ✅ 17 comprehensive tests for BaseService functionality
- ✅ 102/102 tests passing (17 new + 85 existing)

**Key Features Implemented:**
- **BaseService class**: Provides dependency injection capabilities for all services
- **DependencyInjectionMixin**: Can be mixed into existing services without inheritance changes
- **Automatic config injection**: Services receive config via `config` parameter
- **Backward compatibility**: Services work exactly as before when no config is injected
- **Fallback handling**: Graceful fallback to global config when injected config is unavailable
- **Interface documentation**: All service interfaces now include DI guidance and examples

### **Phase 3: Update Configuration Layer (Week 3)**

#### Task 3.1: Migrate Config Class

- [ ] Update `Config` class to use unified factory
- [ ] Remove direct registry usage
- [ ] Maintain existing public API for backward compatibility
- [ ] Update `GlobalConfig` to use new pattern

#### Task 3.2: Update Configuration Access Patterns

- [ ] Update services to receive config via dependency injection
- [ ] Remove direct `Config.get_global()` calls from services
- [ ] Update all broker services to use injected configuration

### **Phase 4: Update Services Layer (Week 4)**

#### Task 4.1: Update BaseAggregator

- [ ] Remove manual service creation methods
- [ ] Use unified factory for service creation
- [ ] Remove hardcoded broker-specific logic
- [ ] Ensure proper dependency injection

#### Task 4.2: Update Registration Setup

- [ ] Create new unified registration function
- [ ] Update `app_config.py` to call unified registration
- [ ] Ensure all brokers are registered consistently

### **Phase 5: Migration and Cleanup (Week 5)**

#### Task 5.1: Gradual Migration

- [ ] Keep old factories operational during transition
- [ ] Update consumers to use unified factory gradually
- [ ] Ensure all tests pass throughout migration

#### Task 5.2: Final Cleanup

- [ ] Remove old `ConfigFactory` and `ConfigRegistry` classes
- [ ] Remove old `ServiceFactory` and `BrokerRegistry` classes
- [ ] Update all imports and references
- [ ] Clean up obsolete test files

#### Task 5.3: Documentation Updates

- [ ] Update architecture documentation
- [ ] Update developer guides
- [ ] Add migration notes for contributors
- [ ] Update API documentation

### **Phase 6: Testing and Validation (Week 6)**

#### Task 6.1: Comprehensive Testing

- [ ] Unit tests for all new components
- [ ] Integration tests for unified factory
- [ ] End-to-end tests for broker workflows
- [ ] Performance tests to ensure no regression

#### Task 6.2: Validation and Monitoring

- [ ] Validate all existing functionality works
- [ ] Monitor for any runtime issues
- [ ] Gather feedback from team members
- [ ] Document any issues and resolutions

## Benefits of Unified Architecture

### **1. Consistency**

- Single pattern for managing all broker components
- Consistent registration and creation workflows
- Unified testing approaches

### **2. Maintainability**

- Single source of truth for broker management
- Easier to add new brokers (register in one place)
- Clearer dependency relationships

### **3. Testability**

- Dependency injection enables better unit testing
- Easier to mock configurations and services
- Clearer separation of concerns

### **4. Extensibility**

- Plugin-like architecture for adding new brokers
- Capability-based service discovery
- Runtime broker registration support

### **5. Performance**

- Unified caching strategies
- Reduced object creation overhead
- Better memory management

### **6. ⭐ MASSIVE REDUCTION IN COMPLEXITY**

- **From 8-10 files modified** → **2 lines added to 1 file**
- **From hardcoded logic everywhere** → **Dynamic broker discovery**
- **From manual error-prone process** → **Automated dependency injection**
- **From scattered documentation** → **Single source of truth**

## Risk Mitigation

### **Backward Compatibility**

- Maintain existing public APIs during transition
- Gradual migration allows for thorough testing
- Rollback plan if issues arise

### **Testing Strategy**

- Comprehensive test coverage for new components
- Integration tests to ensure existing functionality
- Performance benchmarks to detect regressions

### **Team Coordination**

- Clear migration phases with defined deliverables
- Regular checkpoints to assess progress
- Documentation updates throughout process

---

*This document should be updated as implementation progresses and any issues or improvements are discovered.*
