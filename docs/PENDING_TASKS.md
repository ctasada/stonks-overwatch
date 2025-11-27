# Stonks Overwatch - Pending Tasks & Improvements

> **Purpose:** This document tracks pending improvements and technical debt for the Stonks Overwatch project.
>
> **Status:** Living document - Updated as tasks are completed or new ones identified.

## High Priority Tasks

### 1. Repository Layer Architecture

**Status:** Pending
**Effort:** 2-3 days
**Impact:** High - Eliminates code duplication, improves maintainability

**Problem:**

- No base repository class (100% code duplication across repositories)
- Inconsistent ORM vs raw SQL usage
- Poor error handling patterns
- No input validation

**Current Pattern:**

```python
# Each repository duplicates the same patterns
class DegiroTransactionsRepository:
    def __init__(self, db_connection):
        self.db = db_connection

    def get_transactions(self, account_id):
        # Raw SQL with no validation
        query = "SELECT * FROM transactions WHERE account_id = %s"
        return self.db.execute(query, (account_id,))
```

**Proposed Solution:**

```python
class BaseRepository:
    def __init__(self, db_connection):
        self.db = db_connection

    def validate_input(self, data, schema):
        """Centralized validation"""
        pass

    def execute_query(self, query, params=None):
        """Centralized error handling"""
        try:
            return self.db.execute(query, params)
        except Exception as e:
            self.logger.error(f"Query failed: {e}")
            raise RepositoryError(f"Database operation failed: {e}")

class DegiroTransactionsRepository(BaseRepository):
    def get_transactions(self, account_id):
        self.validate_input({'account_id': account_id}, self.schemas.account_id)
        return self.execute_query(
            "SELECT * FROM transactions WHERE account_id = %s",
            (account_id,)
        )
```

**Implementation Steps:**
1. Create `BaseRepository` class with common patterns
2. Add input validation framework
3. Implement centralized error handling
4. Refactor existing repositories to inherit from base
5. Add comprehensive tests

**Dependencies:** None

---

### 2. Complete Database Model Migration

**Status:** Partially Complete (70%)
**Effort:** 1-2 days
**Impact:** High - Ensures financial data precision

**Problem:**
DeGiro models still use CharField for financial balances instead of DecimalField:

```python
# Current - Legacy Implementation
class DeGiroCashMovements(models.Model):
    balance_unsettled_cash = models.CharField(max_length=200, null=True)  # ❌
    balance_flatex_cash = models.CharField(max_length=200, null=True)     # ❌
    balance_total = models.CharField(max_length=200, null=True)           # ❌
    change = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # ✅
```

**Target Implementation:**

```python
class DeGiroCashMovements(models.Model):
    balance_unsettled_cash = models.DecimalField(max_digits=20, decimal_places=10, null=True)
    balance_flatex_cash = models.DecimalField(max_digits=20, decimal_places=10, null=True)
    balance_total = models.DecimalField(max_digits=20, decimal_places=10, null=True)
    change = models.DecimalField(max_digits=10, decimal_places=2, null=True)
```

**Implementation Steps:**
1. Create Django migration for field type changes
2. Add data migration to convert existing CharField data to Decimal
3. Update service layer to handle DecimalField types
4. Update serializers and validators
5. Test thoroughly with existing data
6. Deploy with backward compatibility if needed

**Dependencies:** None (can be done independently)

**Notes:**
- ✅ Bitvavo models already use DecimalField
- ✅ IBKR models already use DecimalField
- ⚠️ Requires careful data migration to preserve existing values

---

## Medium Priority Tasks

### 3. Code Duplication - Data Transformation

**Status:** Pending
**Effort:** 3-4 days
**Impact:** Medium - Reduces maintenance burden

**Problem:**
Data transformation logic is duplicated across multiple services:

```python
# Repeated in DegiroPortfolioService
def transform_portfolio_data(self, raw_data):
    portfolio = []
    for item in raw_data:
        portfolio.append({
            'symbol': item['product'],
            'quantity': float(item['size']),
            'price': float(item['price']),
            'value': float(item['value'])
        })
    return portfolio

# Almost identical in BitvavoPortfolioService
def transform_portfolio_data(self, raw_data):
    portfolio = []
    for item in raw_data:
        portfolio.append({
            'symbol': item['symbol'],
            'quantity': float(item['available']),
            'price': float(item['price']),
            'value': float(item['value'])
        })
    return portfolio
```

**Proposed Solution:**
Create a generic data transformation service with configurable mapping:

```python
class DataTransformerService:
    @staticmethod
    def transform_portfolio_data(raw_data, mapping_config):
        """Generic portfolio data transformation"""
        portfolio = []
        for item in raw_data:
            transformed_item = {}
            for target_key, source_key in mapping_config.items():
                transformed_item[target_key] = item.get(source_key, 0)
            portfolio.append(transformed_item)
        return portfolio

# Usage
class DegiroPortfolioService:
    def transform_portfolio_data(self, raw_data):
        mapping = {
            'symbol': 'product',
            'quantity': 'size',
            'price': 'price',
            'value': 'value'
        }
        return DataTransformerService.transform_portfolio_data(raw_data, mapping)
```

**Implementation Steps:**
1. Create `DataTransformerService` utility
2. Define mapping configurations for each broker
3. Refactor existing services to use transformer
4. Add validation and error handling
5. Update tests

**Dependencies:** None

---

### 4. Complete Cache Migration

**Status:** Partially Complete (60%)
**Effort:** 2-3 days
**Impact:** Medium - Improves scalability and consistency

**Problem:**
Some legacy services still use individual caching dictionaries instead of Django's centralized cache:

```python
# Legacy Pattern
class LegacyService:
    def __init__(self):
        self._cache = {}  # Individual cache dict
        self._cache_ttl = 300
```

**Target Pattern:**

```python
# Modern Pattern (already used in IBKR services)
from django.core.cache import cache

class ModernService:
    CACHE_KEY_PREFIX = "service_name"
    CACHE_TIMEOUT = 3600

    def get_data(self):
        cache_key = f"{self.CACHE_KEY_PREFIX}_data"
        cached_data = cache.get(cache_key)

        if cached_data is None:
            data = self._fetch_data()
            cache.set(cache_key, data, timeout=self.CACHE_TIMEOUT)
            return data

        return cached_data
```

**Implementation Steps:**
1. Identify remaining services with legacy caching
2. Refactor to use Django cache framework
3. Update cache key management
4. Configure appropriate TTLs
5. Test cache behavior
6. Remove legacy cache implementations

**Dependencies:** None

---

### 5. Jobs Module Refactoring

**Status:** Pending
**Effort:** 4-5 days
**Impact:** Medium - Improves extensibility and monitoring

**Problem:**
- Jobs are hardcoded for specific brokers
- No job registration system
- Inconsistent scheduling patterns
- No job execution monitoring

**Current Pattern:**

```python
class JobsScheduler:
    def __init__(self):
        self.jobs = {
            'degiro_portfolio_update': {
                'func': self._update_degiro_portfolio,
                'schedule': '0 */30 * * * *'
            },
            'bitvavo_portfolio_update': {
                'func': self._update_bitvavo_portfolio,
                'schedule': '0 */15 * * * *'
            }
        }
```

**Proposed Solution:**

```python
class JobRegistry:
    def __init__(self):
        self.jobs = {}

    def register_job(self, name, func, schedule, broker=None):
        """Register a job with optional broker association"""
        self.jobs[name] = {
            'func': func,
            'schedule': schedule,
            'broker': broker,
            'last_run': None,
            'status': 'idle'
        }

class GenericPortfolioUpdateJob:
    def __init__(self, broker_name, service_factory):
        self.broker_name = broker_name
        self.service_factory = service_factory

    def execute(self):
        try:
            service = self.service_factory.create_portfolio_service(self.broker_name)
            service.update_portfolio()
            return {'status': 'success', 'broker': self.broker_name}
        except Exception as e:
            return {'status': 'error', 'broker': self.broker_name, 'error': str(e)}
```

**Implementation Steps:**
1. Create `JobRegistry` class
2. Implement generic job classes
3. Add job monitoring and status tracking
4. Refactor existing jobs to use registry
5. Add job management admin interface
6. Implement job execution history

**Dependencies:** None

---

### 6. Middleware Architecture Modernization

**Status:** Pending
**Effort:** 3-4 days
**Impact:** Medium - Enables generic authentication

**Problem:**
- Authentication middleware is hardcoded for DeGiro
- No generic authentication strategy
- Inconsistent session handling across brokers

**Current Pattern:**

```python
# Degiro-specific middleware
class DegiroAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'degiro_session' not in request.session:
            return redirect('degiro_login')
        return self.get_response(request)
```

**Proposed Solution:**

```python
class BrokerAuthStrategy:
    """Base class for broker authentication strategies"""
    def is_authenticated(self, request):
        raise NotImplementedError

    def get_login_url(self):
        raise NotImplementedError

    def validate_session(self, session_data):
        raise NotImplementedError

class GenericBrokerAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.auth_strategies = {
            'degiro': DegiroAuthStrategy(),
            'bitvavo': BitvavoAuthStrategy(),
            'ibkr': IBKRAuthStrategy()
        }

    def __call__(self, request):
        broker_name = self._get_broker_from_request(request)

        if broker_name and broker_name in self.auth_strategies:
            strategy = self.auth_strategies[broker_name]

            if not strategy.is_authenticated(request):
                return redirect(strategy.get_login_url())

        return self.get_response(request)
```

**Implementation Steps:**
1. Create `BrokerAuthStrategy` base class
2. Implement strategy for each broker
3. Create `GenericBrokerAuthMiddleware`
4. Update URL routing to identify broker context
5. Migrate from Degiro-specific middleware
6. Test authentication flows for all brokers

**Dependencies:** None

---

## Low Priority Tasks

### 7. Configuration Management Enhancement

**Status:** Pending
**Effort:** 2-3 days
**Impact:** Low - Nice to have

**Issues:**
- Constants scattered across multiple files
- No environment-specific configuration validation
- Limited configuration documentation

**Proposed Improvements:**
1. Centralize all configuration constants
2. Add configuration validation on startup
3. Create environment-specific config files
4. Document all configuration options
5. Add configuration management admin interface

---

### 8. Logging Standardization

**Status:** Pending
**Effort:** 2-3 days
**Impact:** Low - Improves debugging

**Issues:**
- Inconsistent log formats across services
- Missing contextual information in some logs
- No structured logging (JSON format)

**Proposed Improvements:**
1. Standardize log format across all services
2. Add structured logging (JSON) for production
3. Include request context in all logs
4. Add log aggregation configuration
5. Create logging best practices documentation

---

## Future Enhancements

### 9. Performance Monitoring Dashboard

**Status:** Future
**Effort:** 1-2 weeks
**Impact:** Low - Operational visibility

**Proposed Features:**
- Real-time service performance metrics
- Cache hit rate monitoring
- API call tracking and latency
- Error rate dashboards
- Job execution monitoring

---

### 10. Enhanced Admin Interfaces

**Status:** Future
**Effort:** 1-2 weeks
**Impact:** Low - Improved management

**Proposed Features:**
- Broker configuration management UI
- Job scheduling and monitoring
- Cache management interface
- Service health dashboard
- Error log viewer with filtering

---

## Implementation Roadmap

### Sprint 1 (2 weeks)

- ✅ Priority 1: Implement BaseRepository class
- ✅ Priority 2: Complete DeGiro model migration
- 🔄 Priority 4: Complete cache migration

### Sprint 2 (2 weeks)

- 🔄 Priority 5: Jobs module refactoring
- 🔄 Priority 6: Middleware modernization
- 🔄 Priority 3: Data transformation service

### Sprint 3+ (Future)

- Low priority improvements
- Future enhancements
- Additional monitoring and tooling

---

## How to Contribute

If you're working on any of these tasks:

1. Update the task status in this document
2. Create a feature branch: `feature/task-name`
3. Add tests for your changes
4. Update relevant documentation
5. Submit a pull request with reference to this task

---

## Notes

- Tasks are prioritized by impact on maintainability and extensibility
- Effort estimates are approximate and may vary
- Dependencies should be completed before dependent tasks
- Some tasks can be done in parallel

---

*Last Updated: November 2025*
*Document Status: Active Planning*
