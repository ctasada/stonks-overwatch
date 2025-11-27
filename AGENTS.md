# AGENTS.md

## Purpose

This document provides a concise, structured reference for AI agents (such as GPT, Claude, Gemini, etc.) to understand and assist with the Stonks Overwatch project. It summarizes the architecture, extension points, and key development practices, enabling agents to answer questions, generate code, or plan enhancements effectively.

---

## Quick Reference for AI Agents

### ⚡ Critical Workflow - ALWAYS Follow This Order

**When making code changes, ALWAYS:**

1. **Make your code changes**
2. **Run validation commands** (see [Validation Workflow](#validation-workflow-for-ai-agents))
3. **Fix any issues** that arise
4. **Verify with checklist** (see [Self-Review Checklist](#self-review-checklist-for-ai-agents))

### 🎯 Key Principles

- **ALWAYS use `BrokerFactory`** - Never instantiate services directly
- **ALWAYS implement interfaces** - All services must implement their corresponding interface
- **ALWAYS add type hints** - Required for all function signatures
- **ALWAYS use `StonksLogger`** - Never use `print()`
- **ALWAYS edit `staticfiles/`** - Never edit `static/` directory
- **ALWAYS run `make lint-fix`** - Before committing any code
- **ALWAYS write tests** - For new functionality

### 📋 Most Common Commands

```bash
make lint-fix          # Auto-fix code style (RUN THIS FIRST)
make lint-check        # Verify no linting errors
make test              # Run all tests
make pre-commit-run    # Run all quality checks
make collectstatic     # After editing static files
```

### 🚫 Critical Don'ts

- ❌ Don't instantiate services directly - Use `BrokerFactory`
- ❌ Don't edit files in `static/` - Edit `staticfiles/` instead
- ❌ Don't use `print()` - Use `StonksLogger`
- ❌ Don't skip type hints - They're required
- ❌ Don't use bare `except:` - Always catch specific exceptions
- ❌ Don't hardcode paths - Use environment variables or Django settings

---

## Project Overview

**Stonks Overwatch** is a privacy-first, open-source investment portfolio tracker. It consolidates data from multiple brokers (DEGIRO, Bitvavo, IBKR, and more) and runs entirely on the user's local machine. The system is built with extensibility, modularity, and security in mind.

- **Tech Stack:** Python 3.13+, Django 5.2+, Bootstrap, Charts.js
- **Key Features:** Multi-broker support, real-time tracking, plugin-ready architecture, local-first data, cross-platform (web & native)

---

## Core Architecture

### 1. Service-Oriented Design
- **Layers:**
  - Interface Layer: Type-safe contracts for all services
  - Service Layer: Business logic
  - Repository Layer: Data access
  - Presentation Layer: Django views/templates

### 2. Dependency Injection
- All services use dependency injection for loose coupling and testability.

### 3. Factory Pattern
- Centralized `BrokerFactory` for creating broker-specific services.
- **CRITICAL:** Always use the factory - never instantiate services directly
- Factory automatically handles dependency injection (config, etc.)
- Factory is a singleton - use `BrokerFactory()` to get the instance

**Usage Examples:**

```python
from stonks_overwatch.core.factories.broker_factory import BrokerFactory
from stonks_overwatch.core.service_types import ServiceType

# Get factory instance (singleton)
factory = BrokerFactory()

# Create services - config is automatically injected
portfolio_service = factory.create_service("degiro", ServiceType.PORTFOLIO)
transactions_service = factory.create_service("bitvavo", ServiceType.TRANSACTION)

# Typed helper methods are also available
portfolio_service = factory.create_portfolio_service("degiro")
transaction_service = factory.create_transaction_service("bitvavo")

# Factory can also create configurations
config = factory.create_config("degiro")
```

**❌ WRONG - Don't do this:**
```python
# NEVER instantiate services directly
from stonks_overwatch.services.brokers.degiro.services.portfolio_service import DegiroPortfolioService
service = DegiroPortfolioService()  # ❌ WRONG - Missing config injection
```

**✅ CORRECT - Do this:**
```python
# Always use the factory
factory = BrokerFactory()
service = factory.create_service("degiro", ServiceType.PORTFOLIO)  # ✅ CORRECT
```

### 4. Broker Registry
- Central registry (`BrokerRegistry`) manages broker configurations and service registration.
- Supports dynamic broker registration and configuration validation.

### 5. Exception Management
- Structured exception hierarchy for robust error handling.

---

## Broker Integration

- **Adding a Broker:**
  - Implement required service interfaces (Portfolio, Transaction, Account, Deposit, Dividend, Fee, etc.).
  - Register broker in the `BrokerRegistry` via `registry_setup.py`.
  - Use the factory pattern for service instantiation.
  - Follow the client → repository → service pattern.
- **Time to integrate:** 2-4 hours for experienced developers.
- **Reference:** See `docs/ARCHITECTURE_BROKERS.md` for step-by-step instructions.

### Service Interface Implementation

All broker services must implement the corresponding interface from `core/interfaces/`:

**Complete Example - Portfolio Service:**
```python
from typing import List, Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.core.interfaces.portfolio_service import PortfolioServiceInterface
from stonks_overwatch.services.models import PortfolioEntry, TotalPortfolio
from stonks_overwatch.utils.core.logger import StonksLogger

class MyBrokerPortfolioService(BaseService, PortfolioServiceInterface):
    """
    Portfolio service implementation for MyBroker.

    This service retrieves and manages portfolio data from MyBroker's API.
    """

    def __init__(self, config: Optional[BaseConfig] = None, **kwargs):
        """
        Initialize the portfolio service.

        Args:
            config: Optional broker configuration (injected by factory if not provided)
            **kwargs: Additional keyword arguments
        """
        super().__init__(config, **kwargs)
        self.logger = StonksLogger.get_logger(__name__, "[MYBROKER|PORTFOLIO]")
        # Initialize repositories, clients, etc.
        # self._repository = MyBrokerPortfolioRepository(config)
        # self._client = MyBrokerClient(config)

    @property
    def broker_name(self) -> str:
        """Return the broker name."""
        return "mybroker"

    @property
    def is_connected(self) -> bool:
        """Check if connected to broker API."""
        # Implementation here
        return True

    @property
    def supports_offline_mode(self) -> bool:
        """Check if offline mode is supported."""
        return False

    @property
    def get_portfolio(self) -> List[PortfolioEntry]:
        """
        Retrieve portfolio entries for this broker.

        Returns:
            List of portfolio entries

        Raises:
            BrokerConnectionError: If unable to connect to broker API
        """
        try:
            self.logger.debug("Fetching portfolio data")
            # Implementation here - use self.config and self.base_currency
            # portfolio_data = self._repository.fetch_portfolio()
            # return self._transform_to_portfolio_entries(portfolio_data)
            return []
        except Exception as e:
            self.logger.error(f"Failed to fetch portfolio: {str(e)}")
            raise

    def get_portfolio_total(self, portfolio: Optional[List[PortfolioEntry]] = None) -> TotalPortfolio:
        """
        Calculate total portfolio value.

        Args:
            portfolio: Optional portfolio entries (uses get_portfolio if not provided)

        Returns:
            TotalPortfolio with calculated totals
        """
        if portfolio is None:
            portfolio = self.get_portfolio
        # Implementation here
        return TotalPortfolio(total_value=0.0, currency=self.base_currency)
```

**Key Points:**
- **Inherit from both** the interface and `BaseService` for automatic config injection
- **Use `self.config`** and `self.base_currency` (provided by `BaseService`)
- **Return typed data models** from `services/models.py`
- **Handle errors appropriately** and log using `StonksLogger`
- **Implement all abstract methods** from the interface
- **Add proper docstrings** for all public methods

---

## Plugin Architecture (Planned)

- **Goal:** Move from static broker registry to a dynamic plugin system.
- **Key Features:**
  - Dynamic broker discovery and loading
  - Independent broker distribution as packages
  - Plugin isolation and sandboxing
  - API versioning for compatibility
  - 100% backward compatibility
- **Reference:** See `docs/PLUGIN_ARCHITECTURE.md` for the proposal and implementation guide.

---

## Development Practices

- **Setup:**
  - Use `make start` or `make install` to set up the environment.
  - Use `make update` to update dependencies and regenerate licenses.
  - Docker support available via `make docker-run`.
- **Configuration:**
  - All broker credentials and settings are managed in `config/config.json`.
- **Testing:**
  - Automated and manual testing recommended for all new features and integrations.

---

## Documentation Index

- **Quickstart:** `docs/Quickstart.md`
- **Architecture:** `docs/ARCHITECTURE.md`
- **Broker Integration:** `docs/ARCHITECTURE_BROKERS.md`
- **Plugin System:** `docs/PLUGIN_ARCHITECTURE.md`
- **Developer Guide:** `docs/Developing-Stonks-Overwatch.md`
- **Authentication:** `docs/ARCHITECTURE_AUTHENTICATION.md`
- **FAQ:** `docs/FAQ.md`

---

## AI Agent Guidance

- **For code generation:** Follow the factory and registry patterns. Use dependency injection and type-safe interfaces.
- **For planning:** Reference the plugin architecture proposal for extensibility. Ensure backward compatibility.
- **For answering questions:** Use the documentation index above to locate detailed guides.
- **For troubleshooting:** Check the FAQ and architecture docs for common issues and design patterns.

---

## Code Style and Standards

### Python Code Standards

#### Formatting
- **Line Length:** Maximum 120 characters (configured in Ruff)
- **Indentation:** 4 spaces (no tabs)
- **Quotes:** Double quotes for strings
- **Target Version:** Python 3.13+

#### Import Organization
Imports must be organized in the following order (enforced by Ruff/isort):
1. Future imports (rarely needed in Python 3.13+)
2. Standard library imports
3. Third-party imports (Django, external packages)
4. First-party imports (stonks_overwatch modules)
5. Local folder imports
6. Testing imports (django.test, pytest, pook, unittest)

**Rules:**
- One blank line between import groups
- Alphabetical order within each group
- Use `make lint-fix` to auto-organize imports

**Example:**
```python
from typing import List, Optional

from django.db import models

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.core.factories.broker_factory import BrokerFactory
from stonks_overwatch.core.interfaces.portfolio_service import PortfolioServiceInterface
from stonks_overwatch.services.models import PortfolioEntry
from stonks_overwatch.utils.core.logger import StonksLogger
```

#### Type Hints
- **REQUIRED** for all function signatures (parameters and return types)
- Use `typing` module for complex types (`List`, `Dict`, `Optional`, etc.)
- Use `dataclass` for structured data models

**Example:**
```python
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class PortfolioEntry:
    symbol: str
    quantity: float
    value: Optional[float] = None

def get_portfolio(broker_name: str) -> List[PortfolioEntry]:
    """Retrieve portfolio entries for a specific broker."""
    # implementation
    return []
```

#### Naming Conventions
- **Classes:** `PascalCase` (e.g., `PortfolioService`, `BrokerFactory`)
- **Functions/Methods:** `snake_case` (e.g., `get_portfolio`, `fetch_transactions`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Private attributes:** Prefix with single underscore (e.g., `_internal_cache`)
- **Protected attributes:** Single underscore (e.g., `_helper_method`)

#### Documentation
- **Docstrings required** for:
  - All public classes
  - All public methods/functions
  - Complex private methods
- Use Google-style docstrings:
```python
def calculate_portfolio_value(entries: List[PortfolioEntry], currency: str) -> float:
    """
    Calculate the total portfolio value in the specified currency.

    Args:
        entries: List of portfolio entries to calculate value for
        currency: Target currency code (e.g., 'EUR', 'USD')

    Returns:
        Total portfolio value as a float

    Raises:
        ValueError: If currency is not supported
    """
    pass
```

#### Error Handling
- Use structured exceptions from the project's exception hierarchy (`core/exceptions/`)
- Always provide meaningful error messages
- Log errors appropriately using `StonksLogger` with context
- Never use bare `except:` clauses - always catch specific exceptions
- Use `from e` when re-raising exceptions to preserve stack trace

**Example:**
```python
from stonks_overwatch.core.exceptions import BrokerConnectionError
from stonks_overwatch.utils.core.logger import StonksLogger

logger = StonksLogger.get_logger(__name__, "[PORTFOLIO]")

try:
    result = fetch_data()
except ConnectionError as e:
    logger.error(f"Failed to connect to broker API: {str(e)}")
    raise BrokerConnectionError(f"Unable to fetch portfolio data: {str(e)}") from e
except ValueError as e:
    logger.warning(f"Invalid data received: {str(e)}")
    raise
```

#### Logging Guidelines

**CRITICAL:** Always use `StonksLogger` - never use `print()` statements

**Log Levels:**
- **DEBUG**: Detailed information for diagnosing problems (development only)
- **INFO**: General informational messages (startup, successful operations)
- **WARNING**: Something unexpected happened but application continues
- **ERROR**: Serious problem occurred, operation failed

**Best Practices:**
- Always include context in log messages (broker name, operation, etc.)
- Use structured logging format with f-strings
- Log at appropriate levels

**Example:**
```python
from stonks_overwatch.utils.core.logger import StonksLogger

class PortfolioService:
    def __init__(self, broker_name: str):
        self.logger = StonksLogger.get_logger(__name__, f"[{broker_name.upper()}|PORTFOLIO]")
        self.broker_name = broker_name

    def fetch_portfolio(self) -> List[PortfolioEntry]:
        """Fetch portfolio data."""
        self.logger.debug(f"Starting portfolio fetch for {self.broker_name}")

        try:
            result = self._fetch_data()
            self.logger.info(f"Successfully fetched portfolio for {self.broker_name}: {len(result)} entries")
            return result
        except ConnectionError as e:
            self.logger.error(f"Connection failed for {self.broker_name}: {str(e)}")
            raise
```

### Django-Specific Conventions

#### Django Models
- Use Django ORM for database operations
- Always use `timezone.now()` instead of `datetime.now()` for timezone-aware dates
- Use `select_related()` and `prefetch_related()` to avoid N+1 queries

**Example:**
```python
from django.db import models
from django.utils import timezone

class Portfolio(models.Model):
    broker_name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=20)
    created_at = models.DateTimeField(default=timezone.now)

# ✅ CORRECT - Optimized query
portfolios = Portfolio.objects.select_related("broker").filter(broker_name="degiro")

# ❌ WRONG - N+1 query problem
portfolios = Portfolio.objects.filter(broker_name="degiro")
for p in portfolios:
    print(p.broker.name)  # This causes N+1 queries
```

#### Django Views
- Keep views thin - delegate business logic to services
- Always use Django's `HttpResponse` or `JsonResponse`
- Handle exceptions appropriately

**Example:**
```python
from django.http import JsonResponse
from django.views import View

from stonks_overwatch.core.factories.broker_factory import BrokerFactory
from stonks_overwatch.core.service_types import ServiceType
from stonks_overwatch.utils.core.logger import StonksLogger

logger = StonksLogger.get_logger(__name__, "[VIEWS]")

class PortfolioView(View):
    def get(self, request, broker_name: str) -> JsonResponse:
        """Retrieve portfolio data for a specific broker."""
        try:
            factory = BrokerFactory()
            portfolio_service = factory.create_service(broker_name, ServiceType.PORTFOLIO)

            if not portfolio_service:
                return JsonResponse({"error": f"Broker {broker_name} not found"}, status=404)

            portfolio = portfolio_service.get_portfolio
            return JsonResponse({"portfolio": [entry.__dict__ for entry in portfolio]})
        except Exception as e:
            logger.error(f"Error retrieving portfolio for {broker_name}: {str(e)}")
            return JsonResponse({"error": "Failed to retrieve portfolio"}, status=500)
```

#### Django Migrations
- **NEVER** edit migration files manually - always use `makemigrations`
- Run `make migrate` after creating migrations

#### Async/Await Patterns
- Django views are synchronous by default
- When calling async services from sync views, use `sync_to_async`:
```python
from asgiref.sync import sync_to_async
async_result = await sync_to_async(service.get_portfolio)(PortfolioId.ALL)
```
- When calling sync Django code from async context, use `async_to_sync`:
```python
from asgiref.sync import async_to_sync
result = await async_to_sync(call_command)("migrate", database="demo")
```

### File Organization

```
src/stonks_overwatch/
├── services/
│   ├── brokers/              # Broker-specific implementations
│   │   ├── degiro/
│   │   │   ├── client/       # API client
│   │   │   ├── repositories/ # Data access layer
│   │   │   └── services/     # Business logic
│   │   ├── bitvavo/
│   │   └── ibkr/
│   ├── aggregators/          # Cross-broker aggregation services
│   └── utilities/            # Shared utilities
├── core/
│   ├── interfaces/           # Service interfaces
│   └── registry_setup.py     # Broker registry
├── views/                    # Django views
├── templates/                # HTML templates
├── staticfiles/              # SOURCE static assets (CSS, JS, images) - EDIT THESE
├── static/                   # AUTOGENERATED by collectstatic - DO NOT EDIT
├── utils/                    # Utility functions
└── models.py                 # Django models
```

**Guidelines:**
- New broker implementations go in `services/brokers/<broker_name>/`
- Each broker follows the client → repository → service pattern
- Shared logic goes in `aggregators/` or `utilities/`
- Never mix business logic with views
- Data models (dataclasses) go in `services/models.py` for shared models, or broker-specific `repositories/models.py` for broker-specific models

### Data Models

- Use `@dataclass` for all data models (from `dataclasses` module)
- Shared models go in `services/models.py` (e.g., `PortfolioEntry`, `Transaction`, `Dividend`)
- Broker-specific models go in `brokers/<broker_name>/repositories/models.py`
- Always include type hints for all fields
- Use `Optional` for nullable fields

**Example:**
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class PortfolioEntry:
    """Represents a single portfolio entry."""

    symbol: str
    quantity: float
    value: Optional[float] = None
    currency: str = "EUR"
    last_updated: Optional[datetime] = None
```

### Configuration Management

- Configuration classes inherit from `BaseConfig` in `config/` directory
- Access config via dependency injection in services (use `BaseService`)
- Environment variables:
  - `DEMO_MODE`: Enable demo database mode
  - `STONKS_OVERWATCH_APP`: Indicates native app context
  - `STONKS_OVERWATCH_DATA_DIR`: Data directory path
  - `STONKS_OVERWATCH_CONFIG_DIR`: Config directory path
  - `STONKS_OVERWATCH_LOGS_DIR`: Logs directory path
  - `STONKS_OVERWATCH_CACHE_DIR`: Cache directory path
- Never hardcode paths; use environment variables or Django settings

**CRITICAL - Static Files:**
- **ALWAYS edit files in `staticfiles/`** - This is the source directory
- **NEVER edit files in `static/`** - This directory is autogenerated by Django's `collectstatic` command
- The `static/` folder is created/updated when running `collectstatic` command and any manual changes will be overwritten
- After editing `staticfiles/`, run `make collectstatic` to regenerate `static/` with your changes

---

## How to Run the Application, Tests, and Linting

### Running the Application

- **Initial Setup:**
  - `make start` — Installs dependencies, sets up the database, collects static files, and starts the development server.
  - `make run` — Alias for `make start`.
  - The app will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000).
  - Optional flags:
    - `demo=true` — Run with demo data: `make run demo=true`
    - `debug=true` — Enable debug logging: `make run debug=true`

- **Docker:**
  - `make docker-run` — Build and run the application in Docker containers.

### Running Tests

- `make test` — Run the full test suite using pytest.
- `make coverage` — Run tests with coverage report (HTML output in `htmlcov/`).

### Linting and Code Quality

- **Check code style:**
  - `make lint` or `make lint-check` — Check Python code style using Ruff.
- **Auto-fix code style:**
  - `make lint-fix` — Automatically fix Python code style issues and format code.
- **Check Markdown files:**
  - `make markdown-check` — Check Markdown files for style issues.
- **Auto-fix Markdown files:**
  - `make markdown-fix` — Automatically fix Markdown style issues.

### Additional Useful Commands

- `make help` — List all available Makefile commands.
- `make clean` — Remove temporary files and caches.
- `make collectstatic` — Collect static files from `staticfiles/` to `static/` (run after editing static files).
- `make migrate` — Apply database migrations (runs both `makemigrations` and `migrate`).
- `make pre-commit-install` — Install pre-commit hooks for code quality.
- `make pre-commit-run` — Run all pre-commit hooks on the codebase.

---

## Validation Workflow for AI Agents

### ⚠️ CRITICAL: Always Validate Before Completing Tasks

**AI agents MUST run these commands in sequence after making code changes:**

1. **Auto-Fix Code Style (REQUIRED)**
   ```bash
   make lint-fix
   ```
   Auto-fixes import ordering and formats code. If it fails, check for syntax errors.

2. **Verify Linting (REQUIRED)**
   ```bash
   make lint-check
   ```
   Checks for remaining linting errors. Fix reported issues manually.

3. **Run Tests (REQUIRED)**
   ```bash
   make test
   ```
   Ensures all tests pass. Fix broken tests or add new tests for new functionality.

4. **Check Dependencies (RECOMMENDED)**
   ```bash
   make check-dependencies
   ```
   Only if you added or removed dependencies.

5. **Run Pre-commit Hooks (REQUIRED)**
   ```bash
   make pre-commit-run
   ```
   Runs all quality checks. Fix reported issues.

### Quick Validation Script

```bash
make lint-fix && make lint-check && make test && make pre-commit-run
```

### Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Import ordering errors | Run `make lint-fix` again |
| Type hint errors | Add missing type hints to function signatures |
| Test failures | Fix broken tests or add missing tests |
| Dependency errors | Update `pyproject.toml` |
| Django system check errors | Fix Django configuration issues |

### Testing Guidelines

#### When to Write Tests
- **ALWAYS** write tests for:
  - New service methods
  - New business logic
  - Bug fixes (test should fail before fix, pass after)
  - Data transformation logic
  - API integrations (use mocking)

#### Test Structure
Tests go in `tests/` directory, mirroring the source structure:
```
tests/
├── stonks_overwatch/
│   ├── services/
│   │   ├── brokers/
│   │   │   ├── test_bitvavo_portfolio.py
│   │   │   └── test_degiro_transactions.py
│   │   └── aggregators/
│   └── utils/
```

#### Test Naming Conventions
- **Test files:** `test_<module_name>.py`
- **Test classes:** `Test<ClassName>`
- **Test methods:** `test_<method_name>_<scenario>`

#### Test Example

```python
from unittest.mock import Mock
import pytest

from stonks_overwatch.core.exceptions import BrokerConnectionError
from stonks_overwatch.services.models import PortfolioEntry
from stonks_overwatch.services.brokers.bitvavo.services.portfolio_service import BitvavoPortfolioService

class TestBitvavoPortfolioService:
    def test_get_portfolio_returns_entries(self):
        """Test that get_portfolio returns a list of entries."""
        service = BitvavoPortfolioService()
        mock_entry = PortfolioEntry(symbol="BTC", quantity=1.0, value=50000.0)
        service._repository = Mock()
        service._repository.fetch_portfolio.return_value = [mock_entry]

        result = service.get_portfolio

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].symbol == "BTC"

    def test_get_portfolio_raises_on_connection_error(self):
        """Test that get_portfolio raises error on connection failure."""
        service = BitvavoPortfolioService()
        service._repository = Mock()
        service._repository.fetch_portfolio.side_effect = ConnectionError("Connection failed")

        with pytest.raises(BrokerConnectionError):
            _ = service.get_portfolio
```

#### Mocking Patterns

**Using unittest.mock:**
```python
from unittest.mock import Mock, patch

@patch('stonks_overwatch.services.brokers.degiro.client.DegiroClient.fetch_data')
def test_fetch_data(mock_fetch):
    mock_fetch.return_value = {"data": "test"}
    # Test code here
    assert mock_fetch.called
```

**Using pook for HTTP mocking:**
```python
import pook

@pook.on
def test_fetch_data():
    pook.get("https://api.example.com/data", response_json={"result": "ok"})
    result = fetch_from_api()
    assert result == {"result": "ok"}
```

### Common Pitfalls to Avoid

1. **Don't hardcode paths** — Use Django's settings and path utilities
2. **Don't ignore exceptions silently** — Always log and handle appropriately
3. **Don't use mutable default arguments** — Use `None` and initialize in function
4. **Don't mix sync and async code improperly** — Use `sync_to_async` or `async_to_sync` appropriately
5. **Don't store credentials in code** — Use `config/config.json` and encryption utilities
6. **Don't commit commented-out code** — Remove it; Git tracks history
7. **Don't skip type hints** — They're required for all public APIs
8. **Don't use `print()`** — Use `StonksLogger` for all output
9. **Don't modify Django migrations manually** — Generate them with `makemigrations`
10. **Don't import from tests in production code** — Keep test code isolated
11. **Don't edit files in `static/` directory** — Always edit `staticfiles/` instead; `static/` is autogenerated
12. **Don't instantiate services directly** — Always use `BrokerFactory` for service creation
13. **Don't forget to run `collectstatic`** — After editing static files, regenerate `static/` directory
14. **Don't create services without interfaces** — All services must implement their corresponding interface
15. **Don't use bare `except:` clauses** — Always catch specific exceptions

---

## Troubleshooting Common Issues

### Linting Errors
- **Import ordering errors:** Run `make lint-fix` to auto-fix
- **Type hint errors:** Add type hints to all function parameters and return types
- **Line too long:** Break long lines or use parentheses for implicit line continuation

### Test Failures
- **Tests fail after adding new code:** Check if you broke existing functionality, add tests for new functionality, ensure mocks are set up correctly
- **Import errors in tests:** Check that test imports match the source structure

### Django Issues
- **Migration errors:** Never edit migration files manually, run `make migrate` to create new migrations, check for circular dependencies in models
- **Static files not updating:** Ensure you edited files in `staticfiles/` directory, run `make collectstatic` to regenerate `static/` directory

### Service Creation Issues
- **`BrokerFactoryError` when creating services:** Ensure broker is registered in `registry_setup.py`, check that service implements the correct interface, verify service inherits from `BaseService`
- **Configuration not injected:** Ensure service inherits from `BaseService`, use `BrokerFactory` to create services (don't instantiate directly), check that config class is registered

---

## Self-Review Checklist for AI Agents

**⚠️ CRITICAL: Complete this checklist before finalizing any code changes**

### Code Quality
- [ ] Code follows PEP 8 and project conventions (120 char line length)
- [ ] All functions have type hints (parameters AND return types)
- [ ] Public functions have Google-style docstrings
- [ ] Imports are properly organized (run `make lint-fix` to verify)
- [ ] No unused imports or variables
- [ ] No hardcoded paths, URLs, or magic numbers
- [ ] Code is compatible with Python 3.13+

### Error Handling & Logging
- [ ] Proper error handling with meaningful messages
- [ ] Specific exceptions caught (no bare `except:` clauses)
- [ ] Exceptions re-raised with `from e` to preserve stack trace
- [ ] Logging uses `StonksLogger` (never `print()`)
- [ ] Logging uses appropriate levels (DEBUG/INFO/WARNING/ERROR)
- [ ] Log messages include context (broker name, operation, etc.)

### Architecture & Patterns
- [ ] Services created via `BrokerFactory`, not direct instantiation
- [ ] All services implement their corresponding interface
- [ ] Services inherit from both interface and `BaseService`
- [ ] Code follows the factory/registry patterns where applicable
- [ ] Dependency injection used correctly
- [ ] Async/sync conversions handled correctly (`sync_to_async`/`async_to_sync`)

### Testing
- [ ] Tests written for new functionality
- [ ] Tests follow naming conventions (`test_<method>_<scenario>`)
- [ ] Tests use proper mocking (pook or unittest.mock)
- [ ] All tests pass (`make test`)
- [ ] Test coverage maintained or improved

### Django-Specific
- [ ] Django migrations generated if models changed (`make migrate`)
- [ ] No N+1 query problems (use `select_related`/`prefetch_related`)
- [ ] Views are thin (business logic in services)
- [ ] Timezone-aware dates used (`timezone.now()` not `datetime.now()`)

### Configuration & Dependencies
- [ ] New dependencies added to `pyproject.toml` if needed
- [ ] Configuration externalized to `config/config.json`
- [ ] Sensitive data properly encrypted
- [ ] Environment variables used for paths/config

### Static Files
- [ ] Static files edited in `staticfiles/` directory, NOT in `static/`
- [ ] `make collectstatic` run after editing static files

### Validation
- [ ] `make lint-fix` run and code formatted
- [ ] `make lint-check` passes (no linting errors)
- [ ] `make test` passes (all tests green)
- [ ] `make check-dependencies` passes (if dependencies changed)
- [ ] `make pre-commit-run` passes (all hooks green)

### Compatibility & Best Practices
- [ ] Changes are backward compatible (unless explicitly breaking)
- [ ] No commented-out code (Git tracks history)
- [ ] Code follows project file organization structure
- [ ] Error messages are clear and helpful for users

---

*This file is intended for use by AI agents to provide accurate, context-aware assistance for the Stonks Overwatch project.*
