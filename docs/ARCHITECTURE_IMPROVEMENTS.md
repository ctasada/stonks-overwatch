# Stonks Overwatch - Architecture Improvements (2024 Update)

## Executive Summary

This document presents an up-to-date analysis of the Stonks Overwatch architecture, focusing on maintainability, extensibility, and performance. **Major improvements have been implemented** since the last review, especially in the configuration module, which is now fully registry-based, extensible, and follows Python best practices.

## 🚨 Critical Issues (IMMEDIATE ACTION REQUIRED)

✅ **All critical security issues have been resolved!**

## 🔧 High Priority Improvements

### 1. **Repository Layer Architecture** (HIGH PRIORITY)

**Issues Identified**:

- No base repository class (100% code duplication)
- Inconsistent ORM vs raw SQL usage
- Poor error handling patterns
- No input validation

**Current Pattern**:

```python
# Each repository duplicates the same patterns
class DegiroTransactionsRepository:
    def __init__(self, db_connection):
        self.db = db_connection

    def get_transactions(self, account_id):
        # Raw SQL with no validation
        query = "SELECT * FROM transactions WHERE account_id = %s"
        return self.db.execute(query, (account_id,))

    def save_transaction(self, transaction):
        # No input validation
        query = "INSERT INTO transactions VALUES (%s, %s, %s)"
        return self.db.execute(query, transaction)
```

**Proposed Solution**:

```python
class BaseRepository:
    def __init__(self, db_connection):
        self.db = db_connection

    def validate_input(self, data, schema):
        # Centralized validation
        pass

    def execute_query(self, query, params=None):
        # Centralized error handling
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

**Status**: **Pending**
**Next Step**: Implement a `BaseRepository` class and refactor all repositories to use it.

### 2. **Database Model Inconsistencies** (HIGH PRIORITY)

**Issues Found**:
1. **Missing Foreign Key Relationships**: No relationships between related tables
2. **Type Inconsistencies**: Balance fields stored as strings vs decimals
3. **No Field Validation**: Missing constraints and validators
4. **Inconsistent Naming**: Mixed snake_case and camelCase in field names

**Current Issues**:

```python
# Inconsistent field types
class Transaction(models.Model):
    amount = models.CharField(max_length=50)  # Should be DecimalField
    balance = models.CharField(max_length=50)  # Should be DecimalField
    accountId = models.CharField(max_length=50)  # Inconsistent naming

# Missing relationships
class Portfolio(models.Model):
    # No foreign key to Account
    account_id = models.CharField(max_length=50)

# No validation
class Dividend(models.Model):
    amount = models.CharField(max_length=50)  # No validation for positive amounts
```

**Proposed Solution**:

```python
class Transaction(models.Model):
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    balance = models.DecimalField(max_digits=15, decimal_places=2)
    account_id = models.CharField(max_length=50)  # Consistent naming

    # Add validation
    def clean(self):
        if self.amount <= 0:
            raise ValidationError("Amount must be positive")

    # Add relationships
    account = models.ForeignKey('Account', on_delete=models.CASCADE)
```

**Status**: **Pending**
**Next Step**: Refactor models for proper typing, relationships, and validation.

---

## 🔄 Medium Priority Improvements

### 3. **Code Duplication Patterns** (MEDIUM PRIORITY)

**Issues Found**:
- **Data Transformation**: Same transformation logic repeated across services
- **Error Handling**: Inconsistent error handling patterns
- **Service Creation**: Duplicate service instantiation code

**Current Pattern**:

```python
# Repeated across multiple services
class DegiroPortfolioService:
    def transform_portfolio_data(self, raw_data):
        # Same transformation logic as other services
        portfolio = []
        for item in raw_data:
            portfolio.append({
                'symbol': item['product'],
                'quantity': float(item['size']),
                'price': float(item['price']),
                'value': float(item['value'])
            })
        return portfolio

class BitvavoPortfolioService:
    def transform_portfolio_data(self, raw_data):
        # Almost identical transformation logic
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

**Proposed Solution**:

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

**Status**: **Pending**
**Next Step**: Create shared services for data transformation, error handling, and service instantiation.

### 4. **Caching Architecture** (MEDIUM PRIORITY)

**Issues Found**:
- **No Centralized Cache**: Each service implements its own caching
- **Inconsistent TTL**: Different cache expiration times across services
- **No Cache Invalidation**: Stale data issues
- **Memory Leaks**: No cache size limits

**Current Pattern**:

```python
# Each service has its own cache implementation
class DegiroPortfolioService:
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes

    def get_portfolio(self, account_id):
        cache_key = f"portfolio_{account_id}"
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return cached_data

        # Fetch fresh data
        data = self._fetch_portfolio(account_id)
        self._cache[cache_key] = (data, time.time())
        return data

class BitvavoPortfolioService:
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 600  # Different TTL!

    # Similar caching logic...
```

**Proposed Solution**:

```python
class CacheManager:
    def __init__(self, default_ttl=300, max_size=1000):
        self._cache = {}
        self.default_ttl = default_ttl
        self.max_size = max_size

    def get(self, key):
        if key in self._cache:
            data, timestamp, ttl = self._cache[key]
            if time.time() - timestamp < ttl:
                return data
            else:
                del self._cache[key]
        return None

    def set(self, key, value, ttl=None):
        if len(self._cache) >= self.max_size:
            # Evict oldest entries
            self._evict_oldest()

        ttl = ttl or self.default_ttl
        self._cache[key] = (value, time.time(), ttl)

    def invalidate_pattern(self, pattern):
        """Invalidate all keys matching pattern"""
        keys_to_delete = [k for k in self._cache.keys() if pattern in k]
        for key in keys_to_delete:
            del self._cache[key]

# Usage
cache_manager = CacheManager(default_ttl=300, max_size=1000)

class DegiroPortfolioService:
    def get_portfolio(self, account_id):
        cache_key = f"portfolio_degiro_{account_id}"
        cached_data = cache_manager.get(cache_key)
        if cached_data:
            return cached_data

        data = self._fetch_portfolio(account_id)
        cache_manager.set(cache_key, data, ttl=300)
        return data
```

**Status**: **Pending**
**Next Step**: Implement a centralized, configurable cache manager.

### 5. **Exception Management** (MEDIUM PRIORITY)

**Issues Found**:
- **Inconsistent Exceptions**: Different exception types for similar errors
- **Poor Error Messages**: Generic error messages without context
- **No Error Recovery**: Services fail completely on any error
- **Missing Error Logging**: Errors not properly logged for debugging

**Current Pattern**:

```python
# Inconsistent exception handling
class DegiroPortfolioService:
    def get_portfolio(self, account_id):
        try:
            response = self.client.get_portfolio(account_id)
            return response.json()
        except requests.RequestException as e:
            # Generic exception, no context
            raise Exception(f"Failed to get portfolio: {e}")
        except KeyError as e:
            # Different exception type for similar error
            raise ValueError(f"Invalid response format: {e}")

class BitvavoPortfolioService:
    def get_portfolio(self, account_id):
        try:
            response = self.client.get_portfolio(account_id)
            return response.json()
        except Exception as e:
            # Too broad exception handling
            raise Exception(f"Error: {e}")
```

**Proposed Solution**:

```python
class BrokerServiceException(Exception):
    """Base exception for broker service errors"""
    def __init__(self, message, broker_name, operation, original_error=None):
        self.broker_name = broker_name
        self.operation = operation
        self.original_error = original_error
        super().__init__(f"[{broker_name}] {operation}: {message}")

class AuthenticationError(BrokerServiceException):
    """Authentication failed"""
    pass

class DataFormatError(BrokerServiceException):
    """Invalid data format received"""
    pass

class NetworkError(BrokerServiceException):
    """Network communication failed"""
    pass

# Usage
class DegiroPortfolioService:
    def get_portfolio(self, account_id):
        try:
            response = self.client.get_portfolio(account_id)
            return response.json()
        except requests.RequestException as e:
            raise NetworkError(
                f"HTTP request failed: {e}",
                broker_name="Degiro",
                operation="get_portfolio",
                original_error=e
            )
        except KeyError as e:
            raise DataFormatError(
                f"Missing required field: {e}",
                broker_name="Degiro",
                operation="get_portfolio",
                original_error=e
            )
```

**Status**: **Pending**
**Next Step**: Standardize exception classes and error handling patterns.

### 6. **Jobs Module Architecture** (MEDIUM PRIORITY)

**Issues Found**:
- **Broker-Specific Jobs**: Jobs hardcoded for specific brokers
- **No Job Registration**: Adding new jobs requires code changes
- **Inconsistent Scheduling**: Different scheduling patterns
- **No Job Monitoring**: No visibility into job execution

**Current Pattern**:

```python
# Hardcoded broker-specific jobs
class JobsScheduler:
    def __init__(self):
        self.jobs = {
            'degiro_portfolio_update': {
                'func': self._update_degiro_portfolio,
                'schedule': '0 */30 * * * *'  # Every 30 minutes
            },
            'bitvavo_portfolio_update': {
                'func': self._update_bitvavo_portfolio,
                'schedule': '0 */15 * * * *'  # Every 15 minutes
            }
        }

    def _update_degiro_portfolio(self):
        # Degiro-specific logic
        degiro_service = DegiroPortfolioService()
        degiro_service.update_portfolio()

    def _update_bitvavo_portfolio(self):
        # Bitvavo-specific logic
        bitvavo_service = BitvavoPortfolioService()
        bitvavo_service.update_portfolio()
```

**Proposed Solution**:

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

    def get_jobs_for_broker(self, broker_name):
        """Get all jobs for a specific broker"""
        return {name: job for name, job in self.jobs.items()
                if job['broker'] == broker_name}

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

# Usage
job_registry = JobRegistry()
service_factory = ServiceFactory()

# Register generic jobs for each broker
for broker in ['degiro', 'bitvavo']:
    job = GenericPortfolioUpdateJob(broker, service_factory)
    job_registry.register_job(
        f'{broker}_portfolio_update',
        job.execute,
        schedule='0 */30 * * * *',
        broker=broker
    )
```

**Status**: **Pending**
**Next Step**: Refactor jobs module to be broker-agnostic and extensible.

### 7. **Middleware Architecture** (MEDIUM PRIORITY)

**Issues Found**:
- **Broker-Specific Middleware**: Authentication middleware hardcoded for Degiro
- **No Generic Auth**: Each broker requires its own middleware
- **Inconsistent Session Handling**: Different session management patterns
- **No Auth Strategy Pattern**: No pluggable authentication strategies

**Current Pattern**:

```python
# Degiro-specific middleware
class DegiroAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Hardcoded for Degiro
        if 'degiro_session' not in request.session:
            return redirect('degiro_login')

        # Degiro-specific session validation
        session_data = request.session['degiro_session']
        if not self._is_valid_degiro_session(session_data):
            return redirect('degiro_login')

        return self.get_response(request)

    def _is_valid_degiro_session(self, session_data):
        # Degiro-specific validation logic
        return 'degiro_token' in session_data and \
               session_data.get('expires_at', 0) > time.time()

# No equivalent for other brokers
```

**Proposed Solution**:

```python
class BrokerAuthStrategy:
    """Base class for broker authentication strategies"""
    def __init__(self, broker_name):
        self.broker_name = broker_name

    def is_authenticated(self, request):
        """Check if user is authenticated for this broker"""
        raise NotImplementedError

    def get_login_url(self):
        """Get the login URL for this broker"""
        raise NotImplementedError

    def validate_session(self, session_data):
        """Validate broker-specific session data"""
        raise NotImplementedError

class DegiroAuthStrategy(BrokerAuthStrategy):
    def __init__(self):
        super().__init__('degiro')

    def is_authenticated(self, request):
        return 'degiro_session' in request.session

    def get_login_url(self):
        return 'degiro_login'

    def validate_session(self, session_data):
        return 'degiro_token' in session_data and \
               session_data.get('expires_at', 0) > time.time()

class BitvavoAuthStrategy(BrokerAuthStrategy):
    def __init__(self):
        super().__init__('bitvavo')

    def is_authenticated(self, request):
        return 'bitvavo_session' in request.session

    def get_login_url(self):
        return 'bitvavo_login'

    def validate_session(self, session_data):
        return 'bitvavo_token' in session_data and \
               session_data.get('expires_at', 0) > time.time()

class GenericBrokerAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.auth_strategies = {
            'degiro': DegiroAuthStrategy(),
            'bitvavo': BitvavoAuthStrategy()
        }

    def __call__(self, request):
        # Check which broker the request is for
        broker_name = self._get_broker_from_request(request)

        if broker_name and broker_name in self.auth_strategies:
            strategy = self.auth_strategies[broker_name]

            if not strategy.is_authenticated(request):
                return redirect(strategy.get_login_url())

            # Validate session
            session_key = f'{broker_name}_session'
            if session_key in request.session:
                if not strategy.validate_session(request.session[session_key]):
                    return redirect(strategy.get_login_url())

        return self.get_response(request)

    def _get_broker_from_request(self, request):
        """Extract broker name from request path or parameters"""
        # Implementation depends on URL structure
        if 'degiro' in request.path:
            return 'degiro'
        elif 'bitvavo' in request.path:
            return 'bitvavo'
        return None
```

**Status**: **Pending**
**Next Step**: Refactor authentication middleware to support multiple brokers generically.

---

## 🔧 Low Priority Improvements

### 8. **Configuration Management** (LOW PRIORITY)

**Issues**:
- **Scattered Constants**: Hardcoded values across 20+ files.
- **No Environment-Specific Configuration**.
- **Missing Validation**: No config validation on startup.

### 9. **Logging Standardization** (LOW PRIORITY)

**Issues**:
- **Inconsistent Log Formats**: Different patterns across services
- **Missing Context**: Limited contextual information in logs
- **No Structured Logging**: Plain text only

---

## 📊 Impact Analysis

### Code Quality Impact

- **~500 lines of duplicate code** → **~150 lines** (70% reduction, config module)
- **15+ error handling patterns** → **1 centralized pattern** (pending)
- **6 different service creation patterns** → **1 factory pattern** (pending)
- **3 broker-specific modules** → **Generic extensible modules** (in progress)

### Performance Impact

- **Database query optimization**: 40-60% faster queries with proper indexing (pending)
- **Cache efficiency**: 30-50% cache hit rate improvement (pending)
- **Error recovery**: Reduce error-related downtime by 80% (pending)
- **Job scheduling efficiency**: 50% reduction in scheduler overhead (pending)

### Maintainability Impact

- **Repository maintenance**: 60-70% less code to maintain (pending)
- **Testing coverage**: Enable 90%+ repository test coverage (in progress)
- **Development velocity**: 40% faster feature development (in progress)
- **New broker integration**: 80% faster onboarding with generic modules (config: **done**)

### Extensibility Impact

- **Jobs module**: New brokers auto-registered for scheduling (pending)
- **Authentication**: Single middleware handles all broker authentication (pending)
- **Configuration**: Dynamic broker config registration (**done**)

---

## 🎯 Implementation Roadmap

### Phase 1: Repository & Database Layer (2-3 weeks)

1. **Add input validation** to all repository methods.
2. **Create BaseRepository** with secure patterns.
3. **Refactor all repositories** to extend BaseRepository.
4. **Add proper foreign key relationships** to models.
5. **Fix type inconsistencies** in database fields.
6. **Implement model validation**.

### Phase 2: Code Duplication & Architecture (2-3 weeks)

1. **Create DataTransformerService** for common transformations.
2. **Implement centralized error handling**.
3. **Refactor service creation** to use dependency injection.
4. **Standardize caching patterns**.
5. **Refactor Jobs module** to be broker-agnostic.
6. **Create generic BrokerAuthMiddleware** to replace DeGiro-specific version.

### Phase 3: Configuration & Monitoring (1-2 weeks)

1. **Centralize configuration management**.
2. **Implement structured logging**.
3. **Add performance monitoring**.
4. **Create admin dashboards**.

---

## 📋 Next Steps

### Immediate Actions (This Week)

1. **Set up code scanning** to prevent future vulnerabilities
2. **Begin BaseRepository implementation**.
3. **Start repository input validation**.

### Short Term (Next Month)

1. **Begin BaseRepository implementation**.
2. **Start database model refactoring**.
3. **Implement comprehensive test coverage**.

### Long Term (Next Quarter)

1. **Complete architecture modernization**.
2. **Achieve 90%+ test coverage**.
3. **Implement monitoring dashboards**.
4. **Document all architectural decisions**.

---

## 🔍 Analysis Methodology

This analysis was conducted through:
- **Codebase scanning**: Automated security and quality analysis
- **Pattern recognition**: Identification of duplicate code patterns
- **Architecture review**: Assessment of current design patterns
- **Security audit**: Manual review of data access patterns
- **Performance analysis**: Query and caching pattern review
- **Module architecture review**: Analysis of jobs, middleware, and config modules

**Total Files Analyzed**: 150+
**Security Vulnerabilities Found**: 6 critical (all resolved)
**Code Duplication Instances**: 20+
**Architecture Patterns Identified**: 15+
**Broker-Specific Modules Requiring Refactoring**: 2 (jobs, middleware)

---

*This document reflects the current state as of July 2024 and should be updated as improvements are implemented.*
