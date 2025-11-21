# Broker Integration Guide

## Overview

This guide explains how to add new brokers to the Stonks Overwatch system. The architecture follows a consistent modular pattern that ensures type safety, maintainability, and automatic integration with the aggregation framework.

## 🏗️ **Architecture Overview**

### **3-Layer Architecture**

Every broker follows the same consistent structure:

```
services/brokers/your_broker/
├── __init__.py
├── client/                     # 🔧 API Communication Layer
│   ├── __init__.py
│   ├── your_broker_client.py   # Low-level API client
│   ├── constants.py            # Broker-specific constants
│   └── exceptions.py           # Broker-specific exceptions (optional)
├── services/                   # 🏢 Business Logic Layer
│   ├── __init__.py
│   ├── portfolio_service.py    # Portfolio operations
│   ├── transaction_service.py  # Transaction operations
│   ├── deposit_service.py      # Deposit/cash operations
│   ├── dividend_service.py     # Dividend operations (optional)
│   ├── fee_service.py          # Fee operations (optional)
│   └── account_service.py      # Account overview (optional)
└── repositories/               # 💾 Data Access Layer
    ├── __init__.py
    ├── models.py               # Broker-specific data models
    └── [other_repositories.py] # Additional data access if needed
```

### **Core Principles**

1. **Interface Compliance**: All services must implement the core interfaces
2. **Separation of Concerns**: Clear boundaries between API, business logic, and data
3. **Automatic Integration**: Properly implemented brokers work automatically with aggregators
4. **Type Safety**: Full type hints and interface contracts
5. **Error Handling**: Graceful handling of broker-specific issues

---

## 🚀 **Quick Start: Adding a New Broker**

### **Step 1: Create Directory Structure**

```bash
mkdir -p src/stonks_overwatch/services/brokers/your_broker/{client,services,repositories}
touch src/stonks_overwatch/services/brokers/your_broker/__init__.py
touch src/stonks_overwatch/services/brokers/your_broker/client/__init__.py
touch src/stonks_overwatch/services/brokers/your_broker/services/__init__.py
touch src/stonks_overwatch/services/brokers/your_broker/repositories/__init__.py
```

### **Step 2: Implement Required Services**

Create the minimum required services (portfolio, transaction, deposit):

```python
# services/portfolio_service.py
from typing import List
from stonks_overwatch.core.interfaces.portfolio_service import PortfolioServiceInterface
from stonks_overwatch.services.models import PortfolioEntry, TotalPortfolio, DailyValue

class PortfolioService(PortfolioServiceInterface):
    def get_portfolio(self) -> List[PortfolioEntry]:
        # Implementation here
        pass

    def get_portfolio_total(self) -> TotalPortfolio:
        # Implementation here
        pass

    def calculate_historical_value(self) -> List[DailyValue]:
        # Implementation here
        pass

    def calculate_product_growth(self) -> dict:
        # Implementation here
        pass
```

### **Step 3: Register the Broker**

Add registration in `core/registry_setup.py`:

```python
from stonks_overwatch.services.brokers.your_broker.services.portfolio_service import PortfolioService as YourBrokerPortfolioService
# ... other imports

def register_broker_services() -> None:
    registry = BrokerRegistry()

    # ... existing registrations

    # Register Your Broker services
    registry.register_broker(
        broker_name="your_broker",
        portfolio_service=YourBrokerPortfolioService,
        transaction_service=YourBrokerTransactionService,
        deposit_service=YourBrokerDepositService,
        dividend_service=None,  # Optional
        fee_service=None,       # Optional
        account_service=None,   # Optional
    )
```

### **Step 4: Add Configuration**

Add broker configuration in `config/config.py`:

```python
def is_your_broker_enabled(self, selected_portfolio: PortfolioId) -> bool:
    return (selected_portfolio in [PortfolioId.ALL, PortfolioId.YOUR_BROKER] and
            self.your_broker_config.enabled)
```

---

## 📋 **Detailed Implementation Guide**

### **1. Client Layer (`client/`)**

The client layer handles low-level API communication with the broker.

#### **Example: Basic Client Structure**

```python
# client/your_broker_client.py
import requests
from typing import Dict, Any, Optional
from stonks_overwatch.utils.core.logger import StonksLogger

class YourBrokerClient:
    """
    Low-level API client for YourBroker.

    Handles authentication, API calls, and response parsing.
    """

    def __init__(self):
        self.logger = StonksLogger.get_logger("your_broker.client", "[YOUR_BROKER|CLIENT]")
        self.base_url = "https://api.yourbroker.com"
        self.session = requests.Session()
        self._authenticate()

    def _authenticate(self) -> None:
        """Handle authentication with the broker API."""
        # Implementation here
        pass

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request to broker API."""
        try:
            response = self.session.get(f"{self.base_url}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"API request failed: {e}")
            raise
```

#### **Constants and Configuration**

```python
# client/constants.py
from enum import Enum

class ProductType(Enum):
    STOCK = "stock"
    ETF = "etf"
    CRYPTO = "crypto"
    BOND = "bond"

API_ENDPOINTS = {
    "portfolio": "v1/portfolio",
    "transactions": "v1/transactions",
    "deposits": "v1/deposits",
}

# Rate limiting and retry configuration
MAX_RETRIES = 3
RATE_LIMIT_DELAY = 1.0
```

### **2. Services Layer (`services/`)**

The services layer implements business logic and the core interfaces.

#### **Required Services**

Every broker **must implement** these three core services:

##### **Portfolio Service**

```python
# services/portfolio_service.py
from typing import List
from stonks_overwatch.core.interfaces.portfolio_service import PortfolioServiceInterface
from stonks_overwatch.services.models import PortfolioEntry, TotalPortfolio, ProductType
from ..client.your_broker_client import YourBrokerClient

class PortfolioService(PortfolioServiceInterface):
    def __init__(self):
        self.client = YourBrokerClient()

    def get_portfolio(self) -> List[PortfolioEntry]:
        """Get current portfolio holdings."""
        raw_data = self.client.get("portfolio")

        portfolio_entries = []
        for item in raw_data:
            entry = PortfolioEntry(
                symbol=item["symbol"],
                name=item["name"],
                quantity=float(item["quantity"]),
                current_price=float(item["current_price"]),
                total_value=float(item["total_value"]),
                product_type=ProductType.from_string(item["type"]),
                currency=item["currency"],
                # ... other required fields
            )
            portfolio_entries.append(entry)

        return portfolio_entries

    def get_portfolio_total(self) -> TotalPortfolio:
        """Get portfolio summary/totals."""
        raw_data = self.client.get("portfolio/summary")

        return TotalPortfolio(
            total_value=float(raw_data["total_value"]),
            total_gain_loss=float(raw_data["total_pnl"]),
            total_gain_loss_percentage=float(raw_data["total_pnl_percentage"]),
            currency=raw_data["currency"]
        )

    def calculate_historical_value(self, days: int) -> dict:
        """Get historical portfolio values."""
        raw_data = self.client.get(f"portfolio/history?days={days}")

        # Transform to expected format: {"YYYY-MM-DD": float_value}
        return {
            entry["date"]: float(entry["value"])
            for entry in raw_data
        }

    def calculate_product_growth(self, days: int) -> dict:
        """Get product-specific growth data."""
        raw_data = self.client.get(f"portfolio/growth?days={days}")

        # Transform to expected format
        return {
            item["symbol"]: {
                "current_value": float(item["current_value"]),
                "growth_percentage": float(item["growth_percentage"]),
                "growth_absolute": float(item["growth_absolute"])
            }
            for item in raw_data
        }
```

##### **Transaction Service**

```python
# services/transaction_service.py
from typing import List
from stonks_overwatch.core.interfaces.transaction_service import TransactionServiceInterface
from stonks_overwatch.services.models import Transaction, TransactionType
from ..client.your_broker_client import YourBrokerClient

class TransactionsService(TransactionServiceInterface):
    def __init__(self):
        self.client = YourBrokerClient()

    def get_transactions(self) -> List[Transaction]:
        """Get all transactions."""
        raw_data = self.client.get("transactions")

        transactions = []
        for item in raw_data:
            transaction = Transaction(
                datetime=item["datetime"],
                symbol=item["symbol"],
                name=item["name"],
                transaction_type=TransactionType.from_string(item["type"]),
                quantity=float(item["quantity"]),
                price=float(item["price"]),
                total_amount=float(item["total_amount"]),
                currency=item["currency"],
                fees=float(item.get("fees", 0.0))
            )
            transactions.append(transaction)

        return transactions
```

##### **Deposit Service**

```python
# services/deposit_service.py
from typing import List
from stonks_overwatch.core.interfaces.deposit_service import DepositServiceInterface
from stonks_overwatch.services.models import Deposit, DepositType
from ..client.your_broker_client import YourBrokerClient

class DepositsService(DepositServiceInterface):
    def __init__(self):
        self.client = YourBrokerClient()

    def get_cash_deposits(self) -> List[Deposit]:
        """Get cash deposit/withdrawal history."""
        raw_data = self.client.get("deposits")

        deposits = []
        for item in raw_data:
            deposit = Deposit(
                datetime=item["datetime"],
                description=item["description"],
                type=DepositType.DEPOSIT if item["amount"] > 0 else DepositType.WITHDRAWAL,
                change=float(item["amount"]),
                currency=item["currency"]
            )
            deposits.append(deposit)

        return deposits

    def calculate_cash_account_value(self) -> dict:
        """Get historical cash account values."""
        raw_data = self.client.get("cash/history")

        # Transform to expected format: {"YYYY-MM-DD": float_value}
        return {
            entry["date"]: float(entry["balance"])
            for entry in raw_data
        }
```

#### **Optional Services**

These services are optional but recommended for full functionality:

##### **Dividend Service (Optional)**

```python
# services/dividend_service.py
from typing import List
from stonks_overwatch.core.interfaces.dividend_service import DividendServiceInterface
from stonks_overwatch.services.models import Dividend

class DividendsService(DividendServiceInterface):
    def get_dividends(self) -> List[Dividend]:
        """Get dividend history."""
        # Only implement if broker supports dividends
        # Crypto brokers typically return empty list
        return []
```

##### **Fee Service (Optional)**

```python
# services/fee_service.py
from typing import List
from ..client.your_broker_client import YourBrokerClient

class FeesService:
    def get_fees(self) -> List[dict]:
        """Get fee history."""
        # Implementation here
        pass
```

##### **Account Service (Optional)**

```python
# services/account_service.py
from typing import List
from stonks_overwatch.services.models import AccountOverview

class AccountOverviewService:
    def get_account_overview(self) -> List[AccountOverview]:
        """Get account activity overview."""
        # Implementation here
        pass
```

### **3. Repositories Layer (`repositories/`)**

The repositories layer handles data persistence and caching.

```python
# repositories/models.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class YourBrokerTransaction:
    """Broker-specific transaction model."""
    id: str
    timestamp: datetime
    symbol: str
    quantity: float
    price: float
    fees: float
    transaction_type: str

    @classmethod
    def from_api_response(cls, data: dict) -> 'YourBrokerTransaction':
        """Create instance from API response."""
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            symbol=data["symbol"],
            quantity=float(data["quantity"]),
            price=float(data["price"]),
            fees=float(data.get("fees", 0.0)),
            transaction_type=data["type"]
        )
```

---

## 🔧 **Configuration Integration**

### **Add Broker Configuration**

1. **Create configuration classes** (follow existing patterns in `config/`):

```python
# config/your_broker_config.py
from dataclasses import dataclass
from .base_config import BaseConfig

@dataclass
class YourBrokerConfig(BaseConfig):
    enabled: bool = False
    api_key: str = ""
    sandbox_mode: bool = True
```

2. **Add to main config** in `config/config.py`:

```python
def is_your_broker_enabled(self, selected_portfolio: PortfolioId) -> bool:
    return (selected_portfolio in [PortfolioId.ALL, PortfolioId.YOUR_BROKER] and
            self.your_broker_config.enabled)
```

3. **Add portfolio ID** in `services/models.py`:

```python
class PortfolioId(Enum):
    ALL = "all"
    DEGIRO = "degiro"
    BITVAVO = "bitvavo"
    YOUR_BROKER = "your_broker"  # Add this line
```

---

## 🧪 **Testing Your Integration**

### **1. Unit Tests**

Create comprehensive tests for your services:

```python
# tests/services/your_broker/test_portfolio_service.py
import pytest
from unittest.mock import Mock, patch
from stonks_overwatch.services.brokers.your_broker.services.portfolio_service import PortfolioService

class TestPortfolioService:

    @patch('stonks_overwatch.services.brokers.your_broker.client.your_broker_client.YourBrokerClient')
    def test_get_portfolio(self, mock_client):
        # Setup mock
        mock_client.return_value.get.return_value = [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "quantity": 10,
                "current_price": 150.0,
                "total_value": 1500.0,
                "type": "stock",
                "currency": "USD"
            }
        ]

        # Test
        service = PortfolioService()
        portfolio = service.get_portfolio()

        # Assertions
        assert len(portfolio) == 1
        assert portfolio[0].symbol == "AAPL"
        assert portfolio[0].quantity == 10
```

### **2. Integration Tests**

Test that your broker works with the aggregation framework:

```python
# tests/services/test_your_broker_integration.py
def test_your_broker_portfolio_aggregation():
    """Test that YourBroker integrates with portfolio aggregator."""
    from stonks_overwatch.services.aggregators.portfolio_aggregator import PortfolioAggregatorService
    from stonks_overwatch.services.models import PortfolioId

    aggregator = PortfolioAggregatorService()
    portfolio = aggregator.get_portfolio(PortfolioId.YOUR_BROKER)

    # Should not raise exceptions and return proper format
    assert isinstance(portfolio, list)
```

---

## 🏁 **Registration and Activation**

### **1. Register Services**

Add your broker to `core/registry_setup.py`:

```python
def register_broker_services() -> None:
    registry = BrokerRegistry()

    # ... existing brokers

    # Register YourBroker services
    registry.register_broker(
        broker_name="your_broker",
        portfolio_service=YourBrokerPortfolioService,
        transaction_service=YourBrokerTransactionService,
        deposit_service=YourBrokerDepositService,
        dividend_service=YourBrokerDividendService,  # Optional
        fee_service=YourBrokerFeesService,           # Optional
        account_service=YourBrokerAccountService,    # Optional
    )
```

### **2. Update BaseAggregator (if needed)**

If your broker has special requirements, you may need to update the service creation logic in `core/aggregators/base_aggregator.py`:

```python
def _create_your_broker_service(self) -> Optional[Any]:
    """Create YourBroker service with proper dependencies."""
    try:
        if self._service_type == ServiceType.PORTFOLIO:
            from stonks_overwatch.services.brokers.your_broker.services.portfolio_service import PortfolioService
            return PortfolioService()
        # ... other service types
    except Exception as e:
        self._logger.error(f"Failed to create YourBroker {self._service_type.value} service: {e}")
        return None
```

---

## ✅ **Verification Checklist**

Before considering your broker integration complete:

- [ ] **Core Services Implemented**
  - [ ] ✅ PortfolioService (implements PortfolioServiceInterface)
  - [ ] ✅ TransactionsService (implements TransactionServiceInterface)
  - [ ] ✅ DepositsService (implements DepositServiceInterface)

- [ ] **Architecture Compliance**
  - [ ] ✅ Follows 3-layer structure (client/services/repositories)
  - [ ] ✅ Proper type hints throughout
  - [ ] ✅ Error handling implemented
  - [ ] ✅ Logging added where appropriate

- [ ] **Integration**
  - [ ] ✅ Registered in `core/registry_setup.py`
  - [ ] ✅ Configuration added and tested
  - [ ] ✅ Portfolio ID added to enum

- [ ] **Testing**
  - [ ] ✅ Unit tests for all services
  - [ ] ✅ Integration tests with aggregators
  - [ ] ✅ Configuration tests

- [ ] **Documentation**
  - [ ] ✅ Code documented with docstrings
  - [ ] ✅ README updated if needed
  - [ ] ✅ Configuration example provided

---

## 🎯 **Best Practices**

### **1. Error Handling**

```python
def get_portfolio(self) -> List[PortfolioEntry]:
    try:
        raw_data = self.client.get("portfolio")
        return self._transform_portfolio_data(raw_data)
    except BrokerAPIException as e:
        self.logger.warning(f"Broker API error: {e}")
        return []  # Return empty list rather than crashing
    except Exception as e:
        self.logger.error(f"Unexpected error in get_portfolio: {e}")
        raise  # Re-raise unexpected errors
```

### **2. Rate Limiting**

```python
import time
from functools import wraps

def rate_limit(delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            time.sleep(delay)
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

### **3. Caching**

```python
from functools import lru_cache
from datetime import datetime, timedelta

class PortfolioService:
    def __init__(self):
        self._portfolio_cache = None
        self._portfolio_cache_time = None
        self._cache_duration = timedelta(minutes=5)

    def get_portfolio(self) -> List[PortfolioEntry]:
        now = datetime.now()
        if (self._portfolio_cache is None or
            self._portfolio_cache_time is None or
            now - self._portfolio_cache_time > self._cache_duration):

            self._portfolio_cache = self._fetch_portfolio_from_api()
            self._portfolio_cache_time = now

        return self._portfolio_cache
```

### **4. Data Validation**

```python
from typing import List
from pydantic import BaseModel, validator

class PortfolioEntry(BaseModel):
    symbol: str
    quantity: float
    current_price: float

    @validator('quantity')
    def quantity_must_be_positive(cls, v):
        if v < 0:
            raise ValueError('Quantity must be positive')
        return v

    @validator('current_price')
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v
```

---

## 🔗 **Useful References**

### **Existing Broker Examples**

Study these existing implementations for reference:

- **DeGiro** (`services/brokers/degiro/`) - Complex broker with all features
- **Bitvavo** (`services/brokers/bitvavo/`) - Crypto broker example
- **YFinance** (`services/brokers/yfinance/`) - Market data provider example

### **Core Interfaces**

- `core/interfaces/portfolio_service.py` - Portfolio interface contract
- `core/interfaces/transaction_service.py` - Transaction interface contract
- `core/interfaces/deposit_service.py` - Deposit interface contract
- `core/interfaces/dividend_service.py` - Dividend interface contract

### **Framework Components**

- `core/aggregators/base_aggregator.py` - Base aggregator with helper methods
- `core/factories/broker_registry.py` - Service registration system
- `core/factories/service_factory.py` - Service creation and dependency injection

---

## 🆘 **Troubleshooting**

### **Common Issues**

1. **"Broker not found in registry"**
   - Ensure broker is registered in `core/registry_setup.py`
   - Check that registration is called during app startup

2. **"Service does not implement interface"**
   - Verify all required methods are implemented
   - Check method signatures match interface exactly

3. **"No data collected from broker"**
   - Check broker configuration is enabled
   - Verify API credentials are correct
   - Add logging to debug API calls

4. **Import errors**
   - Ensure all `__init__.py` files are present
   - Check circular import issues
   - Verify Python path includes your broker module

### **Debug Mode**

Enable debug logging to troubleshoot issues:

```python
import logging
logging.getLogger("your_broker").setLevel(logging.DEBUG)
```

---

## 🎉 **Success!**

Once your broker is properly integrated:

1. **Automatic Aggregation**: Your broker data will automatically appear in all aggregators
2. **Type Safety**: Full IntelliSense and type checking support
3. **Error Resilience**: Graceful handling when your broker is unavailable
4. **Configuration**: Easy enable/disable through configuration
5. **Testing**: Comprehensive test coverage for reliability

Your broker is now a first-class citizen in the Stonks Overwatch ecosystem! 🚀

---

**Need help?** Check the existing broker implementations or review the core framework documentation for additional guidance.
