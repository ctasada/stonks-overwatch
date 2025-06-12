# Proposed Module Structure for Stonks Overwatch

## Overview
This structure reorganizes the codebase to support the planned architecture improvements while maintaining clear separation of concerns and consistent patterns across all brokers.

## New Directory Structure

```
src/stonks_overwatch/
├── core/                              # 🆕 Core framework components
│   ├── __init__.py
│   ├── interfaces/                    # 🆕 Service interfaces & contracts
│   │   ├── __init__.py
│   │   ├── broker_service.py          # Base broker service interfaces
│   │   ├── portfolio_service.py       # Portfolio service interface
│   │   ├── transaction_service.py     # Transaction service interface
│   │   ├── deposit_service.py         # Deposit service interface
│   │   └── dividend_service.py        # Dividend service interface
│   ├── factories/                     # 🆕 Service factories & builders
│   │   ├── __init__.py
│   │   ├── service_factory.py         # Central service factory
│   │   ├── portfolio_entry_builder.py # Portfolio entry builder
│   │   └── broker_registry.py         # Broker service registry
│   ├── aggregators/                   # 🆕 Base aggregation logic
│   │   ├── __init__.py
│   │   ├── base_aggregator.py         # Base aggregator class
│   │   └── data_merger.py             # Data merging utilities
│   └── exceptions.py                  # 🆕 Custom exceptions
│
├── services/                          # ♻️ Reorganized services
│   ├── __init__.py
│   ├── models.py                      # 📍 Moved from root (shared models)
│   ├── aggregators/                   # 🆕 Aggregation services
│   │   ├── __init__.py
│   │   ├── portfolio_aggregator.py    # 📁 Moved from root
│   │   ├── deposits_aggregator.py     # 📁 Moved from root
│   │   ├── transactions_aggregator.py # 📁 Moved from root
│   │   ├── dividends_aggregator.py    # 📁 Moved from root
│   │   ├── fees_aggregator.py         # 📁 Moved from root
│   │   └── account_overview_aggregator.py # 📁 Moved from root
│   ├── brokers/                       # 🆕 All broker implementations
│   │   ├── __init__.py
│   │   ├── degiro/                    # ♻️ Reorganized DeGiro services
│   │   │   ├── __init__.py
│   │   │   ├── client/                # 🆕 API client layer
│   │   │   │   ├── __init__.py
│   │   │   │   ├── degiro_client.py   # 📁 Renamed from degiro_service.py
│   │   │   │   ├── constants.py       # 📁 Moved from root
│   │   │   │   └── exceptions.py      # 🆕 DeGiro-specific exceptions
│   │   │   ├── services/              # 🆕 Business logic services
│   │   │   │   ├── __init__.py
│   │   │   │   ├── portfolio_service.py      # 📁 Renamed from portfolio.py
│   │   │   │   ├── transaction_service.py    # 📁 Renamed from transactions.py
│   │   │   │   ├── deposit_service.py        # 📁 Renamed from deposits.py
│   │   │   │   ├── dividend_service.py       # 📁 Renamed from dividends.py
│   │   │   │   ├── fee_service.py            # 📁 Renamed from fees.py
│   │   │   │   ├── account_service.py        # 📁 Renamed from account_overview.py
│   │   │   │   ├── currency_service.py       # 📁 Renamed from currency_converter_service.py
│   │   │   │   └── update_service.py         # 📁 Moved from root
│   │   │   └── repositories/          # 📁 Moved from root repositories/degiro/
│   │   │       ├── __init__.py
│   │   │       ├── base_repository.py        # 🆕 Base repository class
│   │   │       ├── transaction_repository.py # 📁 Moved
│   │   │       ├── cash_movement_repository.py # 📁 Moved
│   │   │       ├── dividend_repository.py    # 📁 Moved
│   │   │       ├── product_quotation_repository.py # 📁 Moved
│   │   │       ├── company_profile_repository.py # 📁 Moved
│   │   │       ├── product_info_repository.py # 📁 Moved
│   │   │       └── models.py                 # 📁 Moved from repositories/degiro/
│   │   ├── bitvavo/                   # ♻️ Reorganized Bitvavo services
│   │   │   ├── __init__.py
│   │   │   ├── client/                # 🆕 API client layer
│   │   │   │   ├── __init__.py
│   │   │   │   ├── bitvavo_client.py  # 📁 Renamed from bitvavo_service.py
│   │   │   │   └── exceptions.py      # 🆕 Bitvavo-specific exceptions
│   │   │   ├── services/              # 🆕 Business logic services
│   │   │   │   ├── __init__.py
│   │   │   │   ├── portfolio_service.py   # 📁 Renamed from portfolio.py
│   │   │   │   ├── transaction_service.py # 📁 Renamed from transactions.py
│   │   │   │   ├── deposit_service.py     # 📁 Renamed from deposits.py
│   │   │   │   ├── fee_service.py         # 📁 Renamed from fees.py
│   │   │   │   └── account_service.py     # 📁 Renamed from account_overview.py
│   │   │   └── repositories/          # 🆕 Missing repositories
│   │   │       ├── __init__.py
│   │   │       ├── base_repository.py # 🆕 Base repository class
│   │   │       └── models.py          # 🆕 Bitvavo models
│   │   ├── yfinance/                  # ♻️ Reorganized YFinance services
│   │   │   ├── __init__.py
│   │   │   ├── client/                # 🆕 API client layer
│   │   │   │   ├── __init__.py
│   │   │   │   ├── yfinance_client.py # 📁 Moved from root
│   │   │   │   └── exceptions.py      # 🆕 YFinance-specific exceptions
│   │   │   ├── services/              # 🆕 Business logic services
│   │   │   │   ├── __init__.py
│   │   │   │   └── market_data_service.py # 📁 Renamed from y_finance.py
│   │   │   └── repositories/          # 📁 Moved from root repositories/yfinance/
│   │   │       ├── __init__.py
│   │   │       ├── base_repository.py # 🆕 Base repository class
│   │   │       └── yfinance_repository.py # 📁 Moved
│   │   └── README.md                  # 🆕 Guide for adding new brokers
│   └── utilities/                     # 🆕 Service-specific utilities
│       ├── __init__.py
│       ├── session_manager.py         # 📁 Moved from root
│       └── data_transformers.py       # 🆕 Common data transformation utilities
│
├── utils/                             # ♻️ Reorganized utilities
│   ├── __init__.py
│   ├── core/                          # 🆕 Core utilities
│   │   ├── __init__.py
│   │   ├── logger.py                  # 📁 Moved from root
│   │   ├── singleton.py               # 📁 Moved from root
│   │   ├── datetime.py                # 📁 Moved from root
│   │   ├── localization.py            # 📁 Moved from root
│   │   └── debug.py                   # 📁 Moved from root
│   ├── database/                      # 🆕 Database utilities
│   │   ├── __init__.py
│   │   └── db_utils.py                # 📁 Moved from root
│   ├── domain/                        # 🆕 Domain-specific utilities
│   │   ├── __init__.py
│   │   └── constants.py               # 📁 Moved from root
│   └── testing/                       # 🆕 Testing utilities
│       ├── __init__.py
│       ├── factories.py               # 🆕 Test data factories
│       └── mocks.py                   # 🆕 Mock objects for testing
│
├── config/                            # ✅ Keep existing (good structure)
│   ├── __init__.py
│   ├── config.py
│   ├── base_config.py
│   ├── base_credentials.py
│   ├── degiro_config.py
│   ├── degiro_credentials.py
│   ├── bitvavo_config.py
│   └── bitvavo_credentials.py
│
├── views/                             # ✅ Keep existing (Django views)
├── templates/                         # ✅ Keep existing (Django templates)
├── static/                            # ✅ Keep existing (Static files)
├── jobs/                              # ✅ Keep existing (Background jobs)
├── middleware/                        # ✅ Keep existing (Django middleware)
├── migrations/                        # ✅ Keep existing (Django migrations)
├── templatetags/                      # ✅ Keep existing (Django template tags)
├── models.py                          # ✅ Keep existing (Django models)
├── admin.py                           # ✅ Keep existing (Django admin)
├── app.py                             # ✅ Keep existing (Main app)
├── settings.py                        # ✅ Keep existing (Django settings)
├── urls.py                            # ✅ Keep existing (Django URLs)
├── wsgi.py                            # ✅ Keep existing (WSGI)
├── asgi.py                            # ✅ Keep existing (ASGI)
└── __init__.py                        # ✅ Keep existing
```

## Key Changes & Benefits

### 1. **Core Framework (`core/`)**
- **New**: Central place for architecture components
- **Benefits**: 
  - Service factory, base aggregator, interfaces live here
  - Clear separation from business logic
  - Easier to test and maintain framework code

### 2. **Clear Service Separation (`services/`)**
- **aggregators/**: All aggregation logic in one place
- **brokers/**: Consistent structure for all broker implementations
- **utilities/**: Service-specific utility functions

### 3. **Consistent Broker Structure**
Each broker now follows the same pattern:
- **client/**: API client and low-level communication
- **services/**: Business logic (portfolio, transactions, etc.)
- **repositories/**: Data access layer

### 4. **Better Utilities Organization (`utils/`)**
- **core/**: General utilities (logger, datetime, etc.)
- **database/**: Database-specific utilities
- **domain/**: Business domain utilities (constants, etc.)
- **testing/**: Testing support utilities

### 5. **Interface-Based Design**
- All services implement common interfaces
- Enables polymorphism and better testing
- Supports the service factory pattern

## Migration Benefits

### Immediate Benefits
1. **Clearer Organization**: Easy to find and organize code
2. **Consistent Patterns**: All brokers follow the same structure
3. **Better Testing**: Isolated components are easier to test
4. **Documentation**: Clear structure makes code self-documenting

### Architecture Support
1. **Service Factory**: Natural place in `core/factories/`
2. **Base Aggregator**: Natural place in `core/aggregators/`
3. **Interfaces**: Natural place in `core/interfaces/`
4. **New Brokers**: Template structure for easy addition

### Future Growth
1. **Plugin Architecture**: Broker registry supports dynamic loading
2. **Microservices**: Clear boundaries for future service extraction
3. **Testing**: Better isolation enables comprehensive testing
4. **Documentation**: Structure itself documents the architecture

## Implementation Strategy

### Phase 1: Foundation (Week 1)
1. Create new directory structure
2. Move files to new locations (maintaining imports)
3. Update import statements
4. Test that everything still works

### Phase 2: Interface Implementation (Week 2)
1. Implement interfaces in `core/interfaces/`
2. Update broker services to implement interfaces
3. Add service registry

### Phase 3: Factory & Aggregator (Week 3)
1. Implement service factory in `core/factories/`
2. Implement base aggregator in `core/aggregators/`
3. Update aggregators to use base class

### Phase 4: Repository Standardization (Week 4)
1. Add missing repositories for Bitvavo
2. Implement base repository class
3. Standardize repository interfaces

## File Movement Summary

### Services Reorganization
```
services/portfolio_aggregator.py       → services/aggregators/portfolio_aggregator.py
services/deposits_aggregator.py        → services/aggregators/deposits_aggregator.py
services/transactions_aggregator.py    → services/aggregators/transactions_aggregator.py
services/dividends_aggregator.py       → services/aggregators/dividends_aggregator.py
services/fees_aggregator.py           → services/aggregators/fees_aggregator.py
services/account_overview_aggregator.py → services/aggregators/account_overview_aggregator.py
services/session_manager.py           → services/utilities/session_manager.py
services/models.py                     → services/models.py (stays)
```

### Broker Services Reorganization
```
services/degiro/degiro_service.py      → services/brokers/degiro/client/degiro_client.py
services/degiro/portfolio.py           → services/brokers/degiro/services/portfolio_service.py
services/degiro/transactions.py        → services/brokers/degiro/services/transaction_service.py
services/degiro/deposits.py            → services/brokers/degiro/services/deposit_service.py
services/degiro/dividends.py           → services/brokers/degiro/services/dividend_service.py
services/degiro/fees.py                → services/brokers/degiro/services/fee_service.py
services/degiro/account_overview.py    → services/brokers/degiro/services/account_service.py
services/degiro/currency_converter_service.py → services/brokers/degiro/services/currency_service.py
services/degiro/update_service.py      → services/brokers/degiro/services/update_service.py
services/degiro/constants.py           → services/brokers/degiro/client/constants.py
```

### Repository Reorganization
```
repositories/degiro/*                  → services/brokers/degiro/repositories/*
repositories/yfinance/*                → services/brokers/yfinance/repositories/*
```

### Utilities Reorganization
```
utils/logger.py                        → utils/core/logger.py
utils/singleton.py                     → utils/core/singleton.py
utils/datetime.py                      → utils/core/datetime.py
utils/localization.py                  → utils/core/localization.py
utils/debug.py                         → utils/core/debug.py
utils/db_utils.py                      → utils/database/db_utils.py
utils/constants.py                     → utils/domain/constants.py
```

## Backwards Compatibility

The restructuring will be done with import aliases to maintain backwards compatibility:

```python
# In services/__init__.py
from .aggregators.portfolio_aggregator import PortfolioAggregatorService
from .brokers.degiro.services.portfolio_service import PortfolioService as DeGiroPortfolioService
# ... etc

# Backwards compatibility imports
from .aggregators.portfolio_aggregator import PortfolioAggregatorService as PortfolioAggregatorService_Old
```

This ensures existing code continues to work while we migrate to the new structure. 