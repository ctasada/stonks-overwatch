# Configuration Module Architecture

## Overview

The configuration module has been refactored to use a **registry-based architecture** that eliminates hardcoded broker references and makes the system highly extensible for new brokers.

## Key Components

### 1. ConfigRegistry (Singleton)

The `ConfigRegistry` class manages broker configurations dynamically:

```python
@singleton
class ConfigRegistry:
    def __init__(self):
        self._broker_configs: Dict[str, BaseConfig] = {}
        self._broker_config_classes: Dict[str, Type[BaseConfig]] = {}
```

**Key Methods:**
- `register_broker_config(broker_name, config_class)`: Register a new broker configuration
- `set_broker_config(broker_name, config)`: Set a broker configuration instance
- `get_broker_config(broker_name)`: Retrieve a broker configuration
- `is_broker_enabled(broker_name, selected_portfolio)`: Check if broker is enabled
- `is_broker_connected(broker_name, selected_portfolio)`: Check if broker is connected

### 2. ConfigFactory (Singleton)

The `ConfigFactory` provides a centralized way to create broker configurations:

```python
@singleton
class ConfigFactory:
    def register_broker_config(self, broker_name: str, config_class: Type[BaseConfig]) -> None
    def create_broker_config(self, broker_name: str, **kwargs) -> Optional[BaseConfig]
    def create_default_broker_config(self, broker_name: str) -> Optional[BaseConfig]
    def create_broker_config_from_dict(self, broker_name: str, data: dict) -> Optional[BaseConfig]
```

### 3. Main Config Class

The main `Config` class now uses the registry internally:

```python
class Config:
    def __init__(self, base_currency, degiro_configuration, bitvavo_configuration):
        self.registry = ConfigRegistry()
        # Configurations are set via the registry

    def is_enabled(self, selected_portfolio: PortfolioId) -> bool:
        # Uses registry to check broker status
```

## Benefits of the New Architecture

### 1. **Eliminates Hardcoded References**

**Before:**
```python
def is_degiro_enabled(self, selected_portfolio: PortfolioId = PortfolioId.ALL) -> bool:
    return self.degiro_configuration.is_enabled() and selected_portfolio in [PortfolioId.ALL, PortfolioId.DEGIRO]

def is_bitvavo_enabled(self, selected_portfolio: PortfolioId = PortfolioId.ALL) -> bool:
    return self.bitvavo_configuration.is_enabled() and selected_portfolio in [PortfolioId.ALL, PortfolioId.BITVAVO]
```

**After:**
```python
def is_enabled(self, selected_portfolio: PortfolioId) -> bool:
    if selected_portfolio == PortfolioId.ALL:
        return any(
            self.registry.is_broker_enabled(broker_name, selected_portfolio)
            for broker_name in self.registry.get_available_brokers()
        )
    else:
        broker_name = selected_portfolio.id
        return self.registry.is_broker_enabled(broker_name, selected_portfolio)
```

### 2. **Reduces Code Duplication**

The registry handles common patterns like:
- Portfolio filtering logic
- Configuration validation
- Connection status checking

### 3. **Enables Easy Extension**

Adding a new broker requires:
1. Create broker configuration class (extends `BaseConfig`)
2. Register with the factory
3. **No modifications to main Config class needed!**

## How to Add a New Broker

### Step 1: Create Broker Configuration

```python
from dataclasses import dataclass
from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.base_credentials import BaseCredentials

@dataclass
class NewBrokerCredentials(BaseCredentials):
    username: str
    password: str

    @classmethod
    def from_dict(cls, data: dict) -> "NewBrokerCredentials":
        if not data:
            return cls("", "")
        return cls(**data)

class NewBrokerConfig(BaseConfig):
    config_key = "new_broker"

    def __init__(self, credentials, enabled=True, custom_setting=None):
        super().__init__(credentials, enabled)
        self.custom_setting = custom_setting

    @classmethod
    def from_dict(cls, data: dict) -> "NewBrokerConfig":
        # Implementation for creating from dict

    @classmethod
    def default(cls) -> "NewBrokerConfig":
        # Implementation for default configuration
```

### Step 2: Register with Factory

```python
from stonks_overwatch.config.config_factory import config_factory

config_factory.register_broker_config("new_broker", NewBrokerConfig)
```

### Step 3: Use in Application

```python
# The main Config class automatically handles the new broker!
config = Config.get_global()
config.registry.is_broker_enabled("new_broker")  # Works automatically

# Import both classes from the same file
from stonks_overwatch.config.new_broker import NewBrokerConfig, NewBrokerCredentials
```

## Migration Guide

### For Existing Code

The refactored `Config` class maintains **backward compatibility**:

```python
# Old code still works:
config.is_degiro_enabled()
config.is_bitvavo_enabled()

# New code can use registry directly:
config.registry.is_broker_enabled("degiro")
config.registry.get_available_brokers()
```

### For New Code

Use the registry-based approach:

```python
# Check if any broker is enabled
config.is_enabled(PortfolioId.ALL)

# Check specific broker
config.registry.is_broker_enabled("degiro")

# Get all available brokers
available_brokers = config.registry.get_available_brokers()
```

## Configuration Access Patterns

### For Production Code (Recommended)
Use cached access for better performance:

```python
# Get cached configuration (recommended for production)
config = Config.get_global()

# Access configuration properties
base_currency = config.base_currency
degiro_config = config.registry.get_broker_config("degiro")
```

### For Tests and Initialization
Use fresh configuration creation:

```python
# Create fresh configuration (for tests, initialization)
config = Config._default()  # Internal method for tests

# Or create from specific data
config = Config.from_dict({})
config = Config.from_json_file("test-config.json")
```

### Migration Guide
The public `Config.default()` method has been removed. Use `Config.get_global()` for all production code:

```python
# Before (no longer available)
config = Config.default()  # ❌ This method no longer exists

# After (uses cached instance)
config = Config.get_global()  # ✅ Recommended approach
```

## Configuration File Format

The configuration file format remains the same:

```json
{
  "base_currency": "EUR",
  "degiro": {
    "enabled": true,
    "credentials": {
      "username": "user",
      "password": "pass"
    }
  },
  "bitvavo": {
    "enabled": false,
    "credentials": {
      "api_key": "key",
      "secret": "secret"
    }
  }
}
```

## Testing

The registry-based approach makes testing easier:

```python
def test_new_broker_config():
    # Register test broker
    config_factory.register_broker_config("test_broker", TestBrokerConfig)

    # Create test configuration
    config = Config._default()  # Internal method for tests

    # Test functionality
    assert config.registry.is_broker_enabled("test_broker") == False
    assert "test_broker" in config.registry.get_available_brokers()
```

## Performance Considerations

- **Singleton Pattern**: Registry and factory are singletons, ensuring single instances
- **Lazy Loading**: Broker-specific connection checks are lazy-loaded to avoid circular dependencies
- **Caching**: Registry caches broker configurations for efficient access

## Future Enhancements

1. **Dynamic Configuration Loading**: Load broker configurations from plugins
2. **Configuration Validation**: Add schema validation for broker configurations
3. **Hot Reloading**: Support for configuration changes without restart
4. **Configuration Encryption**: Encrypt sensitive configuration data

## Conclusion

The registry-based configuration architecture provides:

- ✅ **Extensibility**: Easy to add new brokers
- ✅ **Maintainability**: Reduced code duplication
- ✅ **Testability**: Easier to test individual components
- ✅ **Backward Compatibility**: Existing code continues to work
- ✅ **Type Safety**: Full type hints and validation

This architecture addresses all the issues identified in the architecture improvements document and provides a solid foundation for future broker integrations.
