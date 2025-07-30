# New Broker Integration Guide

## Overview

This guide provides step-by-step instructions for integrating a new broker into the Stonks Overwatch unified architecture. The system uses a unified broker registry and factory pattern that dramatically simplifies the broker addition process.

## Architecture Summary

The unified broker architecture consists of:

- **BrokerRegistry**: Central registry for broker configurations and services
- **BrokerFactory**: Factory for creating broker configurations and services with automatic dependency injection
- **Configuration-Driven Registration**: Declarative broker definitions in a single location
- **Service Interfaces**: Type-safe contracts that all broker services must implement

## Architecture Diagram

The following diagram illustrates how all components work together and where your new broker fits into the system:

```mermaid
graph TB
    %% Core Architecture Components
    subgraph "Core Architecture"
        BR[BrokerRegistry<br/>📋 Central Registry]
        BF[BrokerFactory<br/>🏭 Service Creator]
        BR --> BF
    end

    %% Configuration Layer
    subgraph "Configuration Layer"
        BC[BaseConfig<br/>🔧 Base Class]
        DegiroC[DegiroConfig<br/>🇳🇱 DeGiro]
        BitvavoC[BitvavoConfig<br/>₿ Bitvavo]
        IbkrC[IbkrConfig<br/>📈 IBKR]
        NewC[NewBrokerConfig<br/>➕ Your Broker]

        BC -.-> DegiroC
        BC -.-> BitvavoC
        BC -.-> IbkrC
        BC -.-> NewC
    end

    %% Service Interfaces
    subgraph "Service Interfaces"
        PSI[PortfolioServiceInterface<br/>📊 Portfolio Contract]
        TSI[TransactionServiceInterface<br/>💸 Transaction Contract]
        ASI[AccountServiceInterface<br/>👤 Account Contract]
        DSI[DepositServiceInterface<br/>💰 Deposit Contract]
        DivSI[DividendServiceInterface<br/>💵 Dividend Contract]
        FSI[FeeServiceInterface<br/>💳 Fee Contract]
    end

    %% Service Implementations
    subgraph "DeGiro Services"
        DegiroP[DeGiroPortfolioService]
        DegiroT[DeGiroTransactionService]
        DegiroA[DeGiroAccountService]
        DegiroD[DeGiroDepositService]
        DegiroDiv[DeGiroDividendService]
        DegiroF[DeGiroFeeService]

        PSI -.-> DegiroP
        TSI -.-> DegiroT
        ASI -.-> DegiroA
        DSI -.-> DegiroD
        DivSI -.-> DegiroDiv
        FSI -.-> DegiroF
    end

    subgraph "Bitvavo Services"
        BitvavoP[BitvavoPortfolioService]
        BitvavoT[BitvavoTransactionService]
        BitvavoA[BitvavoAccountService]
        BitvavoD[BitvavoDepositService]
        BitvavoDiv[BitvavoDividendService]
        BitvavoF[BitvavoFeeService]

        PSI -.-> BitvavoP
        TSI -.-> BitvavoT
        ASI -.-> BitvavoA
        DSI -.-> BitvavoD
        DivSI -.-> BitvavoDiv
        FSI -.-> BitvavoF
    end

    subgraph "Your New Broker Services"
        NewP[NewBrokerPortfolioService<br/>➕ Implement This]
        NewT[NewBrokerTransactionService<br/>➕ Implement This]
        NewA[NewBrokerAccountService<br/>➕ Implement This]
        NewD[NewBrokerDepositService<br/>➕ Optional]

        PSI -.-> NewP
        TSI -.-> NewT
        ASI -.-> NewA
        DSI -.-> NewD
    end

    %% Registration Process
    subgraph "Registration Setup"
        RS[registry_setup.py<br/>🔗 BROKER_CONFIGS]
        RS --> BR
    end

    %% Application Flow
    subgraph "Application Flow"
        App[Application Startup<br/>🚀 Initialize]
        Agg[Aggregator Services<br/>📊 Business Logic]
        Views[Web Views<br/>🌐 UI Layer]

        App --> RS
        BF --> Agg
        Agg --> Views
    end

    %% Configuration Registration
    DegiroC --> RS
    BitvavoC --> RS
    IbkrC --> RS
    NewC --> RS

    %% Service Registration
    DegiroP --> RS
    BitvavoP --> RS
    NewP --> RS

    %% Dependency Injection
    BF -.->|"Auto-inject config"| DegiroP
    BF -.->|"Auto-inject config"| BitvavoP
    BF -.->|"Auto-inject config"| NewP

    %% Styling
    classDef coreClass fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef configClass fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef interfaceClass fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef serviceClass fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef newClass fill:#ffebee,stroke:#c62828,stroke-width:3px
    classDef setupClass fill:#f1f8e9,stroke:#33691e,stroke-width:2px

    class BR,BF coreClass
    class BC,DegiroC,BitvavoC,IbkrC,NewC configClass
    class PSI,TSI,ASI,DSI,DivSI,FSI interfaceClass
    class DegiroP,DegiroT,DegiroA,DegiroD,DegiroDiv,DegiroF,BitvavoP,BitvavoT,BitvavoA,BitvavoD,BitvavoDiv,BitvavoF serviceClass
    class NewP,NewT,NewA,NewD,NewC newClass
    class RS,App setupClass
```

### Key Relationships

1. **Configuration Flow**: Your `NewBrokerConfig` extends `BaseConfig` and gets registered in `registry_setup.py`
2. **Service Interfaces**: Your services must implement the required interfaces (`PortfolioServiceInterface`, etc.)
3. **Automatic Wiring**: The `BrokerFactory` automatically injects your config into your services
4. **Registry Integration**: All components are centrally managed by the `BrokerRegistry`
5. **Application Integration**: Aggregator services automatically discover and use your broker

### Component Responsibilities

| Component | Purpose | Your Implementation |
|-----------|---------|-------------------|
| **BrokerRegistry** | Stores all broker configs and services | ✅ Automatic registration |
| **BrokerFactory** | Creates instances with dependency injection | ✅ Automatic service creation |
| **Service Interfaces** | Define contracts for broker operations | ❗ You must implement these |
| **Configuration Classes** | Store broker-specific settings | ❗ You must create this |
| **Service Implementations** | Handle actual broker API calls | ❗ You must implement these |

## Quick Start: Adding a New Broker

### 1. Create Broker Configuration

Create a new configuration file in `src/stonks_overwatch/config/`:

```python
# src/stonks_overwatch/config/newbroker.py
from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.base_credentials import BaseCredentials

class NewBrokerCredentials(BaseCredentials):
    def __init__(self, username: str, password: str, api_key: str = None):
        super().__init__(username, password)
        self.api_key = api_key

class NewBrokerConfig(BaseConfig):
    config_key = "newbroker"

    def __init__(self, credentials: NewBrokerCredentials = None, enabled: bool = True):
        super().__init__(enabled)
        self.credentials = credentials or NewBrokerCredentials("", "")

    @classmethod
    def from_dict(cls, data: dict) -> "NewBrokerConfig":
        credentials_data = data.get("credentials", {})
        credentials = NewBrokerCredentials(
            username=credentials_data.get("username", ""),
            password=credentials_data.get("password", ""),
            api_key=credentials_data.get("api_key", "")
        )
        return cls(
            credentials=credentials,
            enabled=data.get("enabled", True)
        )
```

### 2. Create Service Directory Structure

Create the broker service directory structure:

```bash
mkdir -p src/stonks_overwatch/services/brokers/newbroker/{client,services,repositories}
```

### 3. Implement Required Services

Create service implementations that inherit from the required interfaces:

#### Portfolio Service

```python
# src/stonks_overwatch/services/brokers/newbroker/services/portfolio_service.py
from stonks_overwatch.core.interfaces.portfolio_service import PortfolioServiceInterface

class PortfolioService(PortfolioServiceInterface):
    def __init__(self, config=None):
        super().__init__()
        self.config = config

    def get_portfolio(self):
        """Return portfolio data for this broker."""
        # Implement your portfolio retrieval logic
        return []
```

#### Transaction Service

```python
# src/stonks_overwatch/services/brokers/newbroker/services/transaction_service.py
from stonks_overwatch.core.interfaces.transaction_service import TransactionServiceInterface

class TransactionService(TransactionServiceInterface):
    def __init__(self, config=None):
        super().__init__()
        self.config = config

    def get_transactions(self, start_date=None, end_date=None):
        """Return transaction data for this broker."""
        # Implement your transaction retrieval logic
        return []
```

#### Account Service

```python
# src/stonks_overwatch/services/brokers/newbroker/services/account_service.py
from stonks_overwatch.core.interfaces.account_service import AccountServiceInterface

class AccountService(AccountServiceInterface):
    def __init__(self, config=None):
        super().__init__()
        self.config = config

    def get_account_overview(self):
        """Return account overview data for this broker."""
        # Implement your account overview logic
        return {}
```

#### Additional Services (Optional)

Implement additional services as needed:
- `DepositService` (implements `DepositServiceInterface`)
- `DividendService` (implements `DividendServiceInterface`)
- `FeeService` (implements `FeeServiceInterface`)

### 4. Register the Broker

Add your broker to the unified registry by updating `src/stonks_overwatch/core/registry_setup.py`:

```python
# Import your configuration and services
from stonks_overwatch.config.newbroker import NewBrokerConfig
from stonks_overwatch.services.brokers.newbroker.services.portfolio_service import PortfolioService as NewBrokerPortfolioService
from stonks_overwatch.services.brokers.newbroker.services.transaction_service import TransactionService as NewBrokerTransactionService
from stonks_overwatch.services.brokers.newbroker.services.account_service import AccountService as NewBrokerAccountService

# Add to BROKER_CONFIGS dictionary
BROKER_CONFIGS = {
    # ... existing brokers ...
    "newbroker": {
        "config": NewBrokerConfig,
        "services": {
            ServiceType.PORTFOLIO: NewBrokerPortfolioService,
            ServiceType.TRANSACTION: NewBrokerTransactionService,
            ServiceType.ACCOUNT: NewBrokerAccountService,
            # Add other services as needed:
            # ServiceType.DEPOSIT: NewBrokerDepositService,
            # ServiceType.DIVIDEND: NewBrokerDividendService,
            # ServiceType.FEE: NewBrokerFeeService,
        },
        "supports_complete_registration": True,  # Set to False if missing required services
    },
}
```

## Service Interfaces

All broker services must implement the appropriate interface:

### Required Interfaces

#### PortfolioServiceInterface

```python
class PortfolioServiceInterface(ABC):
    @abstractmethod
    def get_portfolio(self):
        """Get portfolio holdings for this broker."""
        pass
```

#### TransactionServiceInterface

```python
class TransactionServiceInterface(ABC):
    @abstractmethod
    def get_transactions(self, start_date=None, end_date=None):
        """Get transaction history for this broker."""
        pass
```

#### AccountServiceInterface

```python
class AccountServiceInterface(ABC):
    @abstractmethod
    def get_account_overview(self):
        """Get account overview/summary for this broker."""
        pass
```

### Optional Interfaces

#### DepositServiceInterface

```python
class DepositServiceInterface(ABC):
    @abstractmethod
    def get_deposits(self):
        """Get deposit history for this broker."""
        pass

    @abstractmethod
    def calculate_cash_account_value(self):
        """Calculate cash account value."""
        pass
```

#### DividendServiceInterface

```python
class DividendServiceInterface(ABC):
    @abstractmethod
    def get_dividends(self):
        """Get dividend history for this broker."""
        pass
```

#### FeeServiceInterface

```python
class FeeServiceInterface(ABC):
    @abstractmethod
    def get_fees(self):
        """Get fee history for this broker."""
        pass
```

## Configuration File Format

Add your broker configuration to your config JSON file:

```json
{
  "newbroker": {
    "enabled": true,
    "credentials": {
      "username": "your_username",
      "password": "your_password",
      "api_key": "your_api_key"
    }
  }
}
```

## Automatic Integration

Once registered, your broker will automatically:

- ✅ Be available in all aggregator services
- ✅ Receive automatic dependency injection of configurations
- ✅ Work with the portfolio filtering system
- ✅ Be included in the unified factory system
- ✅ Pass interface validation checks

## Benefits of the Unified Architecture

### Before (Legacy System)

- **8-10 files** to modify for each new broker
- **Manual hardcoded checks** throughout the codebase
- **Error-prone process** with multiple failure points
- **Scattered registration** across different systems

### After (Unified System)

- **2 steps** to add a new broker:
  1. Create configuration and services
  2. Add one entry to `BROKER_CONFIGS`
- **Automatic integration** with all system components
- **Type-safe interfaces** with runtime validation
- **Centralized registration** in single location

## Testing Your Broker

The system includes automatic mock service generation for testing. Your broker will work with the existing test infrastructure without additional configuration.

Run tests to validate your integration:

```bash
# Test your specific broker services
python -m pytest tests/stonks_overwatch/services/brokers/newbroker/

# Test integration with aggregators
python -m pytest tests/stonks_overwatch/services/aggregators/
```

## Troubleshooting

### Common Issues

1. **Interface validation errors**: Ensure your services inherit from the correct interfaces
2. **Import errors**: Check that all imports in `registry_setup.py` are correct
3. **Configuration issues**: Verify your config class implements `from_dict()` method
4. **Service initialization**: Ensure services accept optional `config` parameter

### Debug Commands

```python
# Check broker registration status
from stonks_overwatch.core.factories.broker_registry import BrokerRegistry
registry = BrokerRegistry()
print(registry.get_fully_registered_brokers())

# Test service creation
from stonks_overwatch.core.factories.broker_factory import BrokerFactory
factory = BrokerFactory()
service = factory.create_service("newbroker", ServiceType.PORTFOLIO)
print(f"Service created: {service}")
```

## Advanced Features

### Custom Client Implementation

Create a dedicated client for API interactions:

```python
# src/stonks_overwatch/services/brokers/newbroker/client/newbroker_client.py
class NewBrokerClient:
    def __init__(self, config):
        self.config = config
        self.base_url = "https://api.newbroker.com"

    def authenticate(self):
        """Handle authentication with broker API."""
        pass

    def make_request(self, endpoint, params=None):
        """Make authenticated request to broker API."""
        pass
```

### Repository Pattern

Implement data access repositories:

```python
# src/stonks_overwatch/services/brokers/newbroker/repositories/portfolio_repository.py
class PortfolioRepository:
    def __init__(self, client):
        self.client = client

    def fetch_holdings(self):
        """Fetch portfolio holdings from broker API."""
        return self.client.make_request("/portfolio/holdings")
```

This completes the broker integration guide. The unified architecture ensures that adding new brokers is straightforward, type-safe, and automatically integrated with the entire system.
