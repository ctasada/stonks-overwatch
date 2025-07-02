# Configuration Integration Guide

## Overview

The configuration module implements a **registry-based architecture with intelligent caching** that eliminates hardcoded broker references, provides high performance through caching, and makes the system highly extensible for new brokers.

## Architecture Diagram

```mermaid
graph TB
    subgraph "Public API"
        Config[Config Class]
        Config --> |"get_global()"| GlobalConfig
        Config --> |"_default()"| ConfigFactory
    end

    subgraph "Caching Layer"
        GlobalConfig[GlobalConfig Singleton]
        GlobalConfig --> |uses| ConfigFactory
        GlobalConfig --> |caches| Config
    end

    subgraph "Factory Layer"
        ConfigFactory[ConfigFactory Singleton]
        ConfigFactory --> |creates| DegiroConfig
        ConfigFactory --> |creates| BitvavoConfig
        ConfigFactory --> |caches| DefaultConfigs
        ConfigFactory --> |caches| CustomConfigs
    end

    subgraph "Registry Layer"
        Config --> |contains| ConfigRegistry
        ConfigRegistry --> |manages| BrokerConfigs
    end

    subgraph "Broker Configurations"
        DegiroConfig[DegiroConfig]
        BitvavoConfig[BitvavoConfig]
        DegiroConfig --> |extends| BaseConfig
        BitvavoConfig --> |extends| BaseConfig
        BaseConfig --> |contains| BaseCredentials
    end

    subgraph "Credentials"
        DegiroCredentials[DegiroCredentials]
        BitvavoCredentials[BitvavoCredentials]
        DegiroCredentials --> |extends| BaseCredentials
        BitvavoCredentials --> |extends| BaseCredentials
    end

    subgraph "Caching"
        DefaultConfigs[Default Configs Cache]
        CustomConfigs[Custom Configs Cache]
    end

    subgraph "Broker Configs"
        BrokerConfigs[Broker Config Instances]
    end

    style GlobalConfig fill:#e1f5fe
    style ConfigFactory fill:#f3e5f5
    style Config fill:#e8f5e8
    style ConfigRegistry fill:#fff3e0
```

## Key Components

### 1. Config Class (Public API)

The main `Config` class provides the public interface for configuration access:

```python
class Config:
    def __init__(self, base_currency, degiro_configuration, bitvavo_configuration):
        self.base_currency = base_currency
        self.registry = ConfigRegistry()  # Instance-based registry

    @classmethod
    def get_global(cls) -> "Config":
        """Get cached configuration (recommended for production)"""
        return global_config.get_config()

    @classmethod
    def _default(cls) -> "Config":
        """Create fresh configuration (internal use only)"""
        # Creates new instance with default broker configs
```

**Key Methods:**

- `get_global()`: Get cached configuration (production use)
- `_default()`: Create fresh configuration (internal/tests)
- `from_dict()`: Create from dictionary
- `from_json_file()`: Load from JSON file
- `is_enabled()`: Check if any broker is enabled
- `is_enabled_and_connected()`: Check if any broker is enabled and connected

### 2. GlobalConfig (Caching Layer)

The `GlobalConfig` singleton provides cached access to configuration:

```python
@singleton
class GlobalConfig:
    def __init__(self):
        self._config = None
        self._factory = config_factory

    def get_config(self) -> Config:
        """Get cached configuration, creating if necessary"""
        if self._config is None:
            self._config = Config._default()
        return self._config

    def refresh_config(self) -> Config:
        """Force refresh of configuration"""
        self._config = Config._default()
        return self._config

    def clear_cache(self, broker_name: str = None) -> None:
        """Clear configuration cache"""
        self._factory.clear_cache(broker_name)
        self._config = None
```

### 3. ConfigFactory (Factory Layer)

The `ConfigFactory` singleton manages broker configuration creation and caching:

```python
@singleton
class ConfigFactory:
    def __init__(self):
        self._config_classes: Dict[str, Type[BaseConfig]] = {}
        self._default_configs: Dict[str, BaseConfig] = {}  # Cache
        self._config_cache: Dict[str, BaseConfig] = {}     # Cache
        self._cache_enabled = True

    def register_broker_config(self, broker_name: str, config_class: Type[BaseConfig]) -> None
    def create_default_broker_config(self, broker_name: str) -> Optional[BaseConfig]
    def create_broker_config(self, broker_name: str, **kwargs) -> Optional[BaseConfig]
    def create_broker_config_from_dict(self, broker_name: str, data: dict) -> Optional[BaseConfig]
    def clear_cache(self, broker_name: Optional[str] = None) -> None
    def disable_caching(self) -> None  # For tests
```

### 4. ConfigRegistry (Registry Layer)

The `ConfigRegistry` manages broker configurations within each Config instance:

```python
class ConfigRegistry:
    def __init__(self):
        self._broker_configs: Dict[str, BaseConfig] = {}

    def set_broker_config(self, broker_name: str, config: BaseConfig) -> None
    def get_broker_config(self, broker_name: str) -> Optional[BaseConfig]
    def is_broker_enabled(self, broker_name: str, selected_portfolio: PortfolioId) -> bool
    def is_broker_connected(self, broker_name: str, selected_portfolio: PortfolioId) -> bool
    def is_broker_enabled_and_connected(self, broker_name: str, selected_portfolio: PortfolioId) -> bool
```

## How to Add a New Broker Configuration

### Step 1: Create Broker Configuration File

Create a new file `src/stonks_overwatch/config/your_broker.py`:

```python
from dataclasses import dataclass
from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.base_credentials import BaseCredentials

@dataclass
class YourBrokerCredentials(BaseCredentials):
    """Credentials for YourBroker integration."""
    username: str
    password: str
    api_key: str = ""
    api_secret: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "YourBrokerCredentials":
        """Create credentials from dictionary."""
        if not data:
            return cls("", "", "", "")
        return cls(
            username=data.get("username", ""),
            password=data.get("password", ""),
            api_key=data.get("api_key", ""),
            api_secret=data.get("api_secret", "")
        )

class YourBrokerConfig(BaseConfig):
    """Configuration for YourBroker integration."""

    config_key = "your_broker"

    def __init__(self, credentials: YourBrokerCredentials, enabled: bool = True,
                 custom_setting: str = None, update_frequency_minutes: int = 5):
        super().__init__(credentials, enabled)
        self.custom_setting = custom_setting
        self.update_frequency_minutes = update_frequency_minutes

    @classmethod
    def from_dict(cls, data: dict) -> "YourBrokerConfig":
        """Create configuration from dictionary."""
        credentials = YourBrokerCredentials.from_dict(data.get("credentials", {}))
        return cls(
            credentials=credentials,
            enabled=data.get("enabled", True),
            custom_setting=data.get("custom_setting"),
            update_frequency_minutes=data.get("update_frequency_minutes", 5)
        )

    @classmethod
    def default(cls) -> "YourBrokerConfig":
        """Create default configuration."""
        return cls(
            credentials=YourBrokerCredentials("", "", "", ""),
            enabled=False,
            custom_setting=None,
            update_frequency_minutes=5
        )
```

### Step 2: Register with Factory

Add the registration to `src/stonks_overwatch/config/config_factory.py`:

```python
def _register_default_brokers(self) -> None:
    """Register the default broker configurations."""
    self.register_broker_config("degiro", DegiroConfig)
    self.register_broker_config("bitvavo", BitvavoConfig)
    self.register_broker_config("your_broker", YourBrokerConfig)  # Add this line
```

And add the import at the top:

```python
from stonks_overwatch.config.your_broker import YourBrokerConfig
```

### Step 3: Update Config Class

Add the new broker to the `Config` class constructor in `src/stonks_overwatch/config/config.py`:

```python
def __init__(
    self,
    base_currency: Optional[str] = DEFAULT_BASE_CURRENCY,
    degiro_configuration: Optional[DegiroConfig] = None,
    bitvavo_configuration: Optional[BitvavoConfig] = None,
    your_broker_configuration: Optional[YourBrokerConfig] = None,  # Add this
) -> None:
    # ... existing code ...

    # Set broker configurations using the factory
    if degiro_configuration:
        self.registry.set_broker_config("degiro", degiro_configuration)
    if bitvavo_configuration:
        self.registry.set_broker_config("bitvavo", bitvavo_configuration)
    if your_broker_configuration:  # Add this
        self.registry.set_broker_config("your_broker", your_broker_configuration)
```

And update the `from_dict` method:

```python
@classmethod
def from_dict(cls, data: dict) -> "Config":
    base_currency = data.get("base_currency", Config.DEFAULT_BASE_CURRENCY)

    # Use factory to create broker configurations
    degiro_configuration = config_factory.create_broker_config_from_dict(
        "degiro", data.get(DegiroConfig.config_key, {})
    )
    bitvavo_configuration = config_factory.create_broker_config_from_dict(
        "bitvavo", data.get(BitvavoConfig.config_key, {})
    )
    your_broker_configuration = config_factory.create_broker_config_from_dict(  # Add this
        "your_broker", data.get(YourBrokerConfig.config_key, {})
    )

    return cls(base_currency, degiro_configuration, bitvavo_configuration, your_broker_configuration)
```

### Step 4: Add Legacy Methods (Optional)

For backward compatibility, you can add legacy methods to the `Config` class:

```python
def is_your_broker_enabled(self, selected_portfolio: PortfolioId = PortfolioId.ALL) -> bool:
    """Check if YourBroker is enabled."""
    return self.registry.is_broker_enabled("your_broker", selected_portfolio)

def is_your_broker_connected(self, selected_portfolio: PortfolioId = PortfolioId.ALL) -> bool:
    """Check if YourBroker is connected."""
    return self.registry.is_broker_connected("your_broker", selected_portfolio)
```

### Step 5: Use in Application

Your new broker is now automatically integrated:

```python
# Get configuration
config = Config.get_global()

# Check if enabled
if config.is_enabled(PortfolioId.YOUR_BROKER):
    # Your broker is enabled
    pass

# Access configuration
your_broker_config = config.registry.get_broker_config("your_broker")
if your_broker_config and your_broker_config.enabled:
    credentials = your_broker_config.credentials
    # Use credentials for API calls
```

## Configuration File Format

Add your broker configuration to the JSON file:

```json
{
  "base_currency": "EUR",
  "degiro": {
    "enabled": true,
    "credentials": {
      "username": "user",
      "password": "pass",
      "int_account": 123456,
      "totp_secret_key": "ABCDEFGHIJKLMNOP",
      "one_time_password": 123456
    },
    "start_date": "2023-01-01",
    "update_frequency_minutes": 5
  },
  "bitvavo": {
    "enabled": false,
    "credentials": {
      "apikey": "key",
      "apisecret": "secret"
    }
  },
  "your_broker": {
    "enabled": true,
    "credentials": {
      "username": "your_user",
      "password": "your_pass",
      "api_key": "your_api_key",
      "api_secret": "your_api_secret"
    },
    "custom_setting": "custom_value",
    "update_frequency_minutes": 10
  }
}
```

## Testing Your Integration

Create tests for your new broker configuration:

```python
def test_your_broker_config():
    # Create test configuration
    config = Config._default()

    # Test default state
    assert not config.registry.is_broker_enabled("your_broker")

    # Test with enabled configuration
    test_config = YourBrokerConfig(
        credentials=YourBrokerCredentials("test", "test", "key", "secret"),
        enabled=True
    )
    config.registry.set_broker_config("your_broker", test_config)

    assert config.registry.is_broker_enabled("your_broker")
    assert config.is_enabled(PortfolioId.YOUR_BROKER)
```

## Performance Features

### 1. **Intelligent Caching**

- **Default Configs Cache**: Broker default configurations cached once
- **Custom Configs Cache**: Custom configurations cached by parameters
- **Global Config Cache**: Single configuration instance shared across application
- **Cache Control**: Can disable caching for tests

### 2. **Singleton Pattern**

- **ConfigFactory**: Single instance manages all broker configurations
- **GlobalConfig**: Single instance provides cached configuration access
- **Memory Efficiency**: No duplicate configuration objects

### 3. **Lazy Loading**

- **Connection Checks**: Broker-specific connection checks loaded on demand
- **Circular Dependency Prevention**: Lazy imports avoid circular dependencies

## Best Practices

### 1. **Credentials Management**

- Always extend `BaseCredentials` for your broker credentials
- Implement `from_dict()` method for JSON deserialization
- Provide sensible defaults for empty/missing data

### 2. **Configuration Design**

- Extend `BaseConfig` for your broker configuration
- Implement both `from_dict()` and `default()` methods
- Use descriptive `config_key` for JSON mapping
- Include all necessary settings with sensible defaults

### 3. **Integration**

- Register your broker in the factory's `_register_default_brokers()` method
- Update the `Config` class constructor and `from_dict()` method
- Add legacy methods if needed for backward compatibility
- Test your integration thoroughly

### 4. **Error Handling**

- Handle missing or invalid configuration gracefully
- Provide meaningful error messages
- Use type hints for better IDE support

## Benefits

### 1. **Performance**

- ✅ **Cached Access**: Single configuration instance shared across application
- ✅ **Reduced Logging**: Eliminated redundant configuration creation messages
- ✅ **Memory Efficiency**: No duplicate configuration objects
- ✅ **Fast Access**: No file I/O after initial load

### 2. **Extensibility**

- ✅ **Easy Broker Addition**: Register new brokers without modifying core code
- ✅ **Dynamic Registration**: Add/remove brokers at runtime
- ✅ **Type Safety**: Full type hints and validation

### 3. **Maintainability**

- ✅ **Reduced Duplication**: Common patterns handled by registry
- ✅ **Clear Separation**: Each component has a single responsibility
- ✅ **Testability**: Easy to test individual components

### 4. **Developer Experience**

- ✅ **Clean API**: Only `Config.get_global()` for production use
- ✅ **Clear Intent**: Private methods indicate internal use
- ✅ **Consistent Patterns**: Same integration approach for all brokers

## Future Enhancements

1. **Dynamic Configuration Loading**: Load broker configurations from plugins
2. **Configuration Validation**: Add schema validation for broker configurations
3. **Hot Reloading**: Support for configuration changes without a restart
4. **Configuration Encryption**: Encrypt sensitive configuration data
5. **Cache Monitoring**: Add metrics for cache hit rates and performance

## Conclusion

The registry-based configuration architecture with intelligent caching provides a robust foundation for adding new broker integrations. By following the established patterns, you can easily add new brokers while maintaining high performance and code quality.

Key advantages:
- **High Performance**: Cached access eliminates redundant creation
- **Extensibility**: Easy to add new brokers
- **Maintainability**: Reduced code duplication
- **Testability**: Excellent testing support
- **Clean API**: Clear separation between public and internal methods
- **Type Safety**: Full type hints and validation
