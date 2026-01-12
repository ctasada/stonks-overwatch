# Stonks Overwatch - Pending Tasks & Improvements

> **Purpose:** This document tracks pending improvements and technical debt for the Stonks Overwatch project.
>
> **Status:** Living document - Updated as tasks are completed or removed.

## High Priority Tasks

### 1. 🔴 CRITICAL: Remove Plaintext Credential Storage in Session

**Status:** Pending
**Effort:** 4 hours
**Impact:** Critical - Security vulnerability
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issues 1.1, 6.1)

**Problem:**
Credentials for all brokers (DeGiro, Bitvavo, IBKR) stored unencrypted in Django session:

```python
# Current - IBKR example
request.session["ibkr_credentials"] = {
    "access_token": access_token,
    "access_token_secret": access_token_secret,
    "consumer_key": consumer_key,
    "dh_prime": dh_prime,
    "encryption_key": encryption_key,
    "signature_key": signature_key,
}
```

**Security Risks:**

- Credentials readable by anyone with session access
- Exposed in debug logs if Django DEBUG=True
- Vulnerable if session backend is compromised
- Violates security best practices

**Files:**

- `src/stonks_overwatch/views/broker_login.py:310-315` (DeGiro)
- `src/stonks_overwatch/services/brokers/ibkr/services/authentication_service.py:166-173` (IBKR)

**Proposed Solution:**

```python
from stonks_overwatch.services.brokers.encryption_utils import encrypt_dict

# Encrypt credentials before storage
encrypted_creds = encrypt_dict({
    "access_token": access_token,
    "access_token_secret": access_token_secret,
    ...
})

# Store encrypted reference only
request.session[SessionKeys.get_credentials_key("ibkr")] = {
    "encrypted_ref": encrypted_creds,
    "created_at": timezone.now().isoformat(),
}
```

**Implementation Steps:**
1. Use existing `EncryptionUtils` from `services/brokers/encryption_utils.py`
2. Encrypt all credential storage operations
3. Store only encrypted credential reference ID in session
4. Add credential rotation mechanism
5. Implement secure credential cleanup on logout
6. Update all broker authentication services
7. Test encryption/decryption flows

**Dependencies:** None

---

### 2. 🔴 CRITICAL: Fix Hardcoded Portfolio Values (IBKR)

**Status:** Pending
**Effort:** 4 hours
**Impact:** Critical - Incorrect financial data
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 6.8)

**Problem:**
Total deposit/withdrawal hardcoded to 10000.0 for all IBKR users:

```python
# src/stonks_overwatch/services/brokers/ibkr/services/portfolio.py:179
def get_portfolio_total(...) -> TotalPortfolio:
    # FIXME: The value needs to be properly retrieved from IBKR
    tmp_total_portfolio["totalDepositWithdrawal"] = 10000.0  # ❌ HARDCODED!
```

**Business Impact:**
- All portfolio ROI calculations are meaningless
- Users see incorrect performance metrics
- Portfolio totals completely wrong
- Misleading financial information

**Implementation Steps:**
1. Implement proper retrieval from IBKR API
2. Add configuration option as temporary fallback
3. Log warning if API retrieval fails
4. Display clear indicator to user when data is incomplete
5. Remove hardcoded value completely

**Dependencies:** IBKR API integration

---

### 3. 🟡 HIGH: Missing Input Validation - Injection Risk (IBKR)

**Status:** Pending
**Effort:** 3 hours
**Impact:** High - Security vulnerability
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 6.2)

**Problem:**
No validation of credential content, only length checks:

```python
# Only checks length, not content
if len(access_token) < 10 or len(access_token_secret) < 10:
    return {"success": False, "message": "Invalid token format - tokens too short"}
```

**Security Risks:**
- No character set validation (SQL injection, XSS potential)
- No maximum length check (DoS via memory exhaustion)
- No format validation (should be alphanumeric + specific chars)
- Credentials could contain malicious payloads

**Files:**
- `src/stonks_overwatch/services/brokers/ibkr/services/authentication_service.py:73-91`

**Proposed Solution:**

```python
import re

# Define allowed patterns
TOKEN_PATTERN = re.compile(r'^[A-Za-z0-9_-]{10,512}$')
CONSUMER_KEY_PATTERN = re.compile(r'^[A-Za-z0-9_-]{5,256}$')
DH_PRIME_PATTERN = re.compile(r'^[A-Za-z0-9+/=]{10,2048}$')  # Base64

def validate_credentials(...) -> dict:
    if not TOKEN_PATTERN.match(access_token):
        return {"success": False, "message": "Invalid access token format"}

    if not CONSUMER_KEY_PATTERN.match(consumer_key):
        return {"success": False, "message": "Invalid consumer key format"}

    # ... additional validation
```

**Implementation Steps:**
1. Add regex pattern validation for all OAuth fields
2. Implement maximum length checks (prevent DoS)
3. Validate character sets (alphanumeric + allowed special chars)
4. Sanitize inputs before logging
5. Add rate limiting per IP/session
6. Add tests for validation edge cases

**Dependencies:** None

---

### 4. 🟡 HIGH: Fix Performance Issue - Session Validation API Calls

**Status:** Pending
**Effort:** 3 hours
**Impact:** High - Performance degradation
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issues 1.2, 6.3)

**Problem:**
Every authentication check calls real API validation (on every request with middleware):

```python
def is_user_authenticated(self, request: HttpRequest) -> bool:
    # ...
    validation_result = self.validate_credentials(...)  # ⚠️ Real API call every time!
```

**Performance Impact:**
- Called on every authenticated request (via middleware)
- Causes API rate limiting
- Unnecessary CPU cycles under load
- Poor user experience

**Files:**
- `src/stonks_overwatch/services/brokers/bitvavo/services/authentication_service.py:159`
- `src/stonks_overwatch/services/brokers/ibkr/services/authentication_service.py:210-223`

**Proposed Solution:**

```python
def is_user_authenticated(self, request: HttpRequest) -> bool:
    # Simple session check (fast)
    if not request.session.get(SessionKeys.get_authenticated_key("ibkr"), False):
        return False

    # Check if we need to revalidate (cache expired)
    last_validated = request.session.get("ibkr_last_validated")
    if last_validated:
        last_validated_dt = datetime.fromisoformat(last_validated)
        if datetime.now() - last_validated_dt < timedelta(minutes=10):
            # Cache still valid, skip validation
            return True

    # Cache expired - perform validation
    validation_result = self.validate_credentials(...)
    if validation_result["success"]:
        request.session["ibkr_last_validated"] = datetime.now().isoformat()
        return True

    return False
```

**Implementation Steps:**
1. Implement token-based authentication cache with TTL (5-10 minutes)
2. Add `last_validated` timestamp to session
3. Only re-validate if cache expired or explicit validation requested
4. Add configuration for validation cache TTL
5. Monitor cache hit rates

**Dependencies:** None

---

### 5. 🟢 MEDIUM: Implement Session Regeneration After Login

**Status:** Pending
**Effort:** 1 hour
**Impact:** Medium - Session fixation prevention
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 1.3)

**Problem:**
Missing session fixation attack prevention after authentication

**Files:**
- `src/stonks_overwatch/views/broker_login.py:80-129`

**Implementation Steps:**
1. Add `request.session.cycle_key()` after successful authentication
2. Clear previous session data before setting authenticated state
3. Update middleware to handle session transitions properly
4. Add tests for session security

**Dependencies:** None

---

### 6. Repository Layer Architecture

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

### 7. Complete Database Model Migration

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

### 8. Refactor Auto-Authentication to Strategy Pattern

**Status:** Pending
**Effort:** 4 hours
**Impact:** Medium - Reduces duplication (~70 lines)
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 2.5)

**Problem:**
Broker-specific auto-authentication methods follow identical patterns:

```python
def _auto_authenticate_degiro(self, request, credentials) -> dict:
    try:
        auth_service = get_authentication_service()
        auth_result = auth_service.authenticate_user(...)
        if auth_result.is_success:
            request.session[f"degiro_authenticated"] = True
            return {"success": True, ...}
    except Exception as e:
        return {"success": False, ...}

# Almost identical patterns for bitvavo and ibkr
```

**Files:**
- `src/stonks_overwatch/views/login.py:234-303`

**Proposed Solution:**

```python
class BrokerAuthenticationStrategy:
    """Base strategy for broker authentication."""

    @abstractmethod
    def get_auth_service(self, config):
        """Return broker-specific authentication service."""
        pass

    @abstractmethod
    def prepare_credentials(self, credentials):
        """Transform credentials for broker-specific format."""
        pass

    def authenticate(self, request, credentials, broker_name):
        """Common authentication flow."""
        try:
            auth_service = self.get_auth_service(config)
            auth_params = self.prepare_credentials(credentials)
            result = auth_service.authenticate_user(request, **auth_params)

            if result.get("success"):
                request.session[f"{broker_name}_authenticated"] = True
            return result
        except Exception as e:
            return {"success": False, "message": str(e)}

# Register strategies
BROKER_STRATEGIES = {
    BrokerName.DEGIRO.value: DegiroAuthStrategy(),
    BrokerName.BITVAVO.value: BitvavoAuthStrategy(),
    BrokerName.IBKR.value: IbkrAuthStrategy(),
}
```

**Implementation Steps:**
1. Create `BrokerAuthenticationStrategy` base class
2. Implement concrete strategies for each broker
3. Update `_attempt_auto_authentication()` to use registry
4. Remove individual `_auto_authenticate_*()` methods
5. Add tests for strategy pattern

**Dependencies:** None

---

### 9. Create ConfigurationManager Utility

**Status:** Pending
**Effort:** 3 hours
**Impact:** Medium - Centralizes configuration management (~40 lines saved)
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 2.6)

**Problem:**
Cache clearing + job reconfiguration pattern scattered across multiple files:

```python
# Duplicated in authentication_service.py and settings.py
self._clear_broker_cache()
self._reset_bitvavo_client()
self._reconfigure_jobs()
```

**Files:**
- `src/stonks_overwatch/services/brokers/bitvavo/services/authentication_service.py:274-330`
- `src/stonks_overwatch/views/settings.py:148-188`

**Proposed Solution:**

```python
class ConfigurationManager:
    """Centralized configuration change management."""

    @staticmethod
    def refresh_after_config_change(
        broker_name: Optional[str] = None,
        reset_singletons: Optional[List[Type]] = None,
        trigger_update: bool = False
    ):
        """
        Refresh system state after configuration changes.

        Args:
            broker_name: Specific broker that changed (for logging)
            reset_singletons: List of singleton classes to reset
            trigger_update: Whether to trigger immediate portfolio update
        """
        logger = StonksLogger.get_logger("config_manager", "[CONFIG_MGR]")

        try:
            # Clear all broker caches
            BrokerFactory().clear_cache()
            logger.debug("Cleared broker factory cache")

            # Reset specified singletons
            if reset_singletons:
                for singleton_cls in reset_singletons:
                    reset_singleton(singleton_cls)
                    logger.debug(f"Reset singleton: {singleton_cls.__name__}")

            # Reconfigure job scheduler
            if JobsScheduler.scheduler:
                JobsScheduler._configure_jobs()
                logger.info("Reconfigured job scheduler")

            # Optionally trigger immediate update
            if trigger_update and broker_name:
                JobsScheduler._update_broker_portfolio(broker_name)
                logger.info(f"Triggered {broker_name} portfolio update")

        except Exception as e:
            logger.error(f"Error refreshing configuration: {str(e)}")
            raise ConfigurationRefreshError(f"Failed to refresh config: {e}")
```

**Implementation Steps:**
1. Create `src/stonks_overwatch/core/configuration_manager.py`
2. Update `authentication_service.py` to use ConfigurationManager
3. Update `settings.py` to use ConfigurationManager
4. Remove duplicate methods
5. Add tests

**Dependencies:** None

---

### 10. Improve Singleton Implementation Architecture

**Status:** Pending
**Effort:** 2 hours
**Impact:** Medium - Better encapsulation
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 2.8)

**Problem:**
Singleton registry uses module-level globals:

```python
# Module-level globals
_singleton_instances: dict[type, Any] = {}
_singleton_locks: dict[type, Lock] = {}
```

**Files:**
- `src/stonks_overwatch/utils/core/singleton.py:7-9, 38-43`

**Proposed Solution:**

```python
class SingletonRegistry:
    """Thread-safe singleton instance registry."""
    _instances: Dict[type, Any] = {}
    _locks: Dict[type, Lock] = {}
    _registry_lock = Lock()

    @classmethod
    def register(cls, singleton_cls: type) -> None:
        """Register a new singleton class."""
        with cls._registry_lock:
            if singleton_cls not in cls._instances:
                cls._instances[singleton_cls] = None
                cls._locks[singleton_cls] = Lock()

    @classmethod
    def get_instance(cls, singleton_cls: type) -> Optional[Any]:
        """Get singleton instance if exists."""
        return cls._instances.get(singleton_cls)

    @classmethod
    def set_instance(cls, singleton_cls: type, instance: Any) -> None:
        """Set singleton instance."""
        cls._instances[singleton_cls] = instance

    @classmethod
    def reset(cls, singleton_cls: type) -> None:
        """Reset a singleton instance."""
        with cls._registry_lock:
            if singleton_cls in cls._instances:
                with cls._locks[singleton_cls]:
                    cls._instances[singleton_cls] = None

    @classmethod
    def get_all_singletons(cls) -> List[type]:
        """Get list of all registered singleton classes."""
        return list(cls._instances.keys())
```

**Implementation Steps:**
1. Create `SingletonRegistry` class
2. Update `singleton` decorator to use registry
3. Update `reset_singleton` to use registry
4. Maintain backward compatibility
5. Add tests

**Dependencies:** None

---

### 11. Add Comprehensive Type Hints

**Status:** Partially Complete (60%)
**Effort:** 1 hour (remaining work)
**Impact:** Medium - Better IDE support
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 2.9)

**Completed Work:**
- ✅ BrokerName enum type hints across entire codebase
- ✅ Configuration layer (BaseConfig, LazyConfig) fully typed
- ✅ Repository methods with proper type constraints
- ✅ JobsScheduler with Union type hints
- ✅ AuthenticationCredentialService with proper types

**Remaining Work:**
Some view and service methods still lack complete type hints:

```python
# Missing return type
def _get_broker_with_stored_credentials(self):
    return broker_name

# Missing parameter types
def _attempt_auto_authentication(self, request, broker_name):
    return {"success": True}

# Missing Dict value types
def _auto_authenticate_degiro(self, request, credentials) -> dict:
    return {}
```

**Implementation Steps:**
1. Add complete type hints to remaining view methods
2. Add type hints to authentication service helper methods
3. Use `TypedDict` for structured dictionaries where appropriate
4. Run `mypy` to validate type correctness
5. Update AGENTS.md with type hint guidelines

**Dependencies:** None

---

### 12. IBKR: Extract Duplicate Retry Logic

**Status:** Pending
**Effort:** 2 hours
**Impact:** High - Removes ~60 lines duplication
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 6.9)

**Problem:**
Identical retry logic duplicated in two methods:

```python
# In get_portfolio() and __get_total_cash() - EXACT SAME PATTERN
self.ibkr_service.get_portfolio_accounts()
time.sleep(0.2)
max_retries = 2

for attempt in range(max_retries):
    try:
        account_summary = self.ibkr_service.get_account_summary()
        break
    except Exception as e:
        error_msg = str(e).lower()
        if "please query /accounts first" in error_msg and attempt < max_retries - 1:
            self.ibkr_service.get_portfolio_accounts()
            time.sleep(0.5)
        else:
            self.logger.error(f"Failed to get account summary...")
```

**Files:**
- `src/stonks_overwatch/services/brokers/ibkr/services/portfolio.py:32-63, 205-236`

**Proposed Solution:**

```python
def _get_account_summary_with_retry(self, max_attempts: int = 2) -> dict:
    """
    Get account summary with automatic retry on session initialization errors.

    Returns:
        Account summary dictionary

    Raises:
        IbkrApiError: If all retry attempts fail
    """
    self.ibkr_service.get_portfolio_accounts()
    time.sleep(self.config.API_SESSION_INIT_DELAY)

    for attempt in range(max_attempts):
        try:
            return self.ibkr_service.get_account_summary()
        except Exception as e:
            if "please query /accounts first" in str(e).lower() and attempt < max_attempts - 1:
                self.logger.warning(
                    f"IBKR API session not ready (attempt {attempt + 1}/{max_attempts}), retrying..."
                )
                self.ibkr_service.get_portfolio_accounts()
                time.sleep(self.config.API_RETRY_DELAY * (attempt + 1))  # Exponential backoff
            else:
                raise

    return None

# Usage:
account_summary = self._get_account_summary_with_retry()
```

**Implementation Steps:**
1. Extract retry logic into private method
2. Replace hardcoded delays with configuration
3. Add exponential backoff
4. Update both call sites
5. Add tests

**Dependencies:** None

---

### 13. IBKR: Fix Overly Broad Exception Catching

**Status:** Pending
**Effort:** 1 hour
**Impact:** High - Code quality & debugging
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 6.10)

**Problem:**
Catching all exceptions including system exceptions:

```python
except Exception as e:  # ⚠️ Catches ALL exceptions including SystemExit
    self.logger.error(f"Error creating portfolio entry: {e}")
```

**Files:**
- `src/stonks_overwatch/services/brokers/ibkr/services/portfolio.py:71, 223`

**Proposed Solution:**

```python
try:
    entry = self.__create_portfolio_entry(position, base_currency)
    portfolio.append(entry)
except (ValueError, KeyError, TypeError) as e:
    # Expected data validation errors
    self.logger.error(
        f"Invalid position data for {position.get('ticker', 'unknown')}: {type(e).__name__}"
    )
except ConnectionError as e:
    # Network/API errors
    self.logger.error(f"API connection error: {type(e).__name__}")
    raise  # Re-raise to fail fast
except Exception as e:
    # Unexpected errors - log with full traceback
    self.logger.exception(f"Unexpected error processing position: {type(e).__name__}")
```

**Implementation Steps:**
1. Replace with specific exception types
2. Allow system exceptions to propagate
3. Add better error context
4. Document expected exceptions

**Dependencies:** None

---

### 14. IBKR: Add Type Safety with Dataclasses

**Status:** Pending
**Effort:** 3 hours
**Impact:** Medium - Type safety
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 6.4)

**Problem:**
Methods return `dict` instead of typed objects:

```python
def validate_credentials(...) -> dict:  # ⚠️ Should be ValidationResult
def authenticate_user(...) -> dict:     # ⚠️ Should be AuthenticationResult
```

**Proposed Solution:**

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ValidationResult:
    """Result of credential validation."""
    success: bool
    message: str
    account_info: Optional[dict] = None

@dataclass
class AuthenticationResult:
    """Result of authentication attempt."""
    success: bool
    message: str
    account_info: Optional[dict] = None
    requires_2fa: bool = False

def validate_credentials(...) -> ValidationResult:
    return ValidationResult(
        success=True,
        message="Credentials validated successfully",
        account_info={"consumer_key": consumer_key[:8] + "..."}
    )
```

**Implementation Steps:**
1. Create typed response dataclasses
2. Update all methods to return typed objects
3. Update tests to use typed responses
4. Add type hints to all method signatures

**Dependencies:** None

---

### 15. IBKR: Fix Bare Exception Catching in Registry

**Status:** Pending
**Effort:** 1 hour
**Impact:** Medium - Code quality
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 6.5)

**Problem:**
Catching all exceptions during service imports:

```python
except Exception as e:  # ⚠️ Too broad
    logger.warning(f"Could not import BitvavoAuthenticationService: {e}")
    BitvavoAuthenticationService = None
```

**Files:**
- `src/stonks_overwatch/core/registry_setup.py:35-39, 65-69, 95-99`

**Proposed Solution:**

```python
except (ImportError, ModuleNotFoundError, AttributeError) as e:
    logger.warning(f"Could not import BitvavoAuthenticationService: {e}")
    BitvavoAuthenticationService = None
```

**Implementation Steps:**
1. Replace with specific exception types
2. Allow system exceptions to propagate
3. Add better error messages

**Dependencies:** None

---

### 16. IBKR: Make Magic Numbers Configurable

**Status:** Pending
**Effort:** 1.5 hours
**Impact:** Medium - Configuration management
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 6.11)

**Problem:**
Retry attempts and delays hardcoded:

```python
time.sleep(0.2)  # Why 0.2 seconds?
max_retries = 2  # Why 2 attempts?
time.sleep(0.5)  # Why 0.5 seconds?
```

**Files:**
- `src/stonks_overwatch/services/brokers/ibkr/services/portfolio.py:40, 45, 59, 208, 211, 231`

**Proposed Solution:**

```python
# In config/ibkr.py
class IbkrPortfolioConfig:
    """Configuration for IBKR portfolio service timing and retries."""

    # API session initialization
    API_SESSION_INIT_DELAY = 0.2  # seconds - Time for IBKR to process /accounts call

    # Retry configuration
    API_MAX_RETRY_ATTEMPTS = 2  # Maximum retry attempts for failed API calls
    API_RETRY_DELAY = 0.5  # seconds - Base delay between retries
    API_RETRY_BACKOFF = 1.5  # Exponential backoff multiplier

    # Supported currencies for cash balance
    SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP", "CHF", "JPY"]

    # Cache configuration
    PORTFOLIO_CACHE_TTL = 1800  # seconds (30 minutes)

# Usage:
time.sleep(self.config.API_SESSION_INIT_DELAY)
for attempt in range(self.config.API_MAX_RETRY_ATTEMPTS):
    time.sleep(self.config.API_RETRY_DELAY * (self.config.API_RETRY_BACKOFF ** attempt))
```

**Implementation Steps:**
1. Create configuration class for IBKR timing
2. Document reasoning for timing choices
3. Make configurable via environment variables
4. Add to AGENTS.md configuration section

**Dependencies:** None

---

### 17. Add Comprehensive View Tests

**Status:** Pending
**Effort:** 6 hours
**Impact:** Medium - Test coverage
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 4.1)

**Problem:**
New views lack dedicated test files:

- `src/stonks_overwatch/views/broker_login.py` (400 lines, no tests)
- `src/stonks_overwatch/views/root_redirect.py` (167 lines, no tests)

**Implementation Steps:**
1. Create `tests/stonks_overwatch/views/test_broker_login_view.py`
2. Create `tests/stonks_overwatch/views/test_root_redirect.py`
3. Test all broker authentication flows (DEGIRO TOTP, Bitvavo API, IBKR OAuth)
4. Test session state transitions
5. Test error handling and edge cases
6. Test security scenarios (invalid credentials, session fixation)
7. Use parameterized tests to reduce duplication

**Dependencies:** None

---

### 18. Add Integration Tests for Auth Middleware Stack

**Status:** Pending
**Effort:** 4 hours
**Impact:** Medium - Integration testing
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 4.2)

**Problem:**
Current tests heavily rely on mocks, missing integration scenarios

**Files:**
- `tests/stonks_overwatch/middleware/test_authentication.py`

**Implementation Steps:**
1. Add integration tests with real Django request/response cycle
2. Test middleware chain: `AuthenticationMiddleware` → `DeGiroAuthMiddleware`
3. Test session state across multiple requests
4. Test concurrent authentication attempts

**Dependencies:** None

---

### 19. Parameterize Duplicate Test Cases

**Status:** Pending
**Effort:** 3 hours
**Impact:** Medium - Test maintainability
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 4.3)

**Problem:**
Similar test patterns repeated for each broker

**Proposed Solution:**

```python
@pytest.mark.parametrize("broker,credentials", [
    ("degiro", {"username": "user", "password": "pass"}),
    ("bitvavo", {"api_key": "key", "api_secret": "secret"}),
    ("ibkr", {"access_token": "token"}),
])
def test_successful_login(broker, credentials):
    # ...
```

**Implementation Steps:**
1. Use `@pytest.mark.parametrize` for broker-specific tests
2. Extract common test setup to fixtures
3. Reduce test duplication

**Dependencies:** None

---

### 20. Fix Currency Detection in Bitvavo Portfolio Service

**Status:** Pending
**Effort:** 2 hours
**Impact:** Medium - Multi-currency support
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 5.1)

**Problem:**
Hardcoded EUR check breaks multi-currency support:

```python
@staticmethod
def __is_currency(symbol: str) -> bool:
    return symbol == "EUR"  # ❌ Hardcoded!
```

**Files:**
- `src/stonks_overwatch/services/brokers/bitvavo/services/portfolio_service.py:60-61`

**Implementation Steps:**
1. Make currency list configurable in `BitvavoConfig`
2. Add `SUPPORTED_CURRENCIES = ["EUR", "USD", "GBP"]` to config
3. Update method to check against config list
4. Add test for multi-currency portfolios

**Dependencies:** None

---

### 21. Add Safeguard for Price Fetch Failures

**Status:** Pending
**Effort:** 2 hours
**Impact:** Medium - Data accuracy
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 5.2)

**Problem:**
Double-fetch failure returns 0, causing incorrect portfolio valuation

**Files:**
- `src/stonks_overwatch/services/brokers/bitvavo/services/portfolio_service.py:318-325`

**Implementation Steps:**
1. Add retry logic with exponential backoff
2. Return `None` instead of 0 when both fetches fail
3. Log critical error with symbol and retry count
4. Display warning to user about missing prices in UI

**Dependencies:** None

---

### 22. Fix Timezone Handling in Update Service

**Status:** Pending
**Effort:** 1 hour
**Impact:** Medium - Schedule correctness
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 5.3)

**Problem:**
Hardcoded UTC assumption causes schedule issues in other timezones:

```python
last_movement = self._get_last_cash_movement_import().replace(tzinfo=timezone.utc)
```

**Files:**
- `src/stonks_overwatch/services/brokers/degiro/services/update_service.py:165-166`

**Implementation Steps:**
1. Use `django.utils.timezone.make_aware()` instead of `.replace()`
2. Respect configured timezone from settings
3. Add timezone validation tests

**Dependencies:** None

---

### 23. Make Cache TTL Configurable

**Status:** Pending
**Effort:** 1 hour
**Impact:** Medium - Configurability
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 5.4)

**Problem:**
1-hour cache TTL hardcoded, may be too long for active trading

**Files:**
- `src/stonks_overwatch/services/brokers/degiro/services/update_service.py:47`

**Implementation Steps:**
1. Add `PORTFOLIO_CACHE_TTL` to Django settings
2. Default to 1800 seconds (30 minutes)
3. Allow override via environment variable
4. Document in configuration guide

**Dependencies:** None

---

### 24. Code Duplication - Data Transformation

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

### 25. Complete Cache Migration

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

### 26. Jobs Module Refactoring

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

### 27. Middleware Architecture Modernization

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

### 28. Fix Keyboard Navigation for Broker Selector (WCAG Critical)

**Status:** Pending
**Effort:** 2 hours
**Impact:** Low - Accessibility
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 3.1)

**Problem:**
Broker cards use `<div onclick>` - not keyboard accessible

```html
<div class="card broker-card h-100" onclick="selectBroker('{{ broker.name }}')">
```

**Files:**
- `src/stonks_overwatch/templates/login.html:85, 112-114`

**Implementation Steps:**
1. Replace `<div>` with semantic `<a>` or `<button>` elements
2. Add proper `href` or `role="button"` with keyboard handlers
3. Add focus styles for keyboard navigation
4. Test with screen reader (VoiceOver/NVDA)

**Dependencies:** None

---

### 29. Add Accessible Tooltips for IBKR Help Icons

**Status:** Pending
**Effort:** 3 hours
**Impact:** Low - Accessibility
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 3.2)

**Problem:**
Help tooltips only work on hover, not accessible to keyboard users

**Files:**
- `src/stonks_overwatch/templates/login/ibkr_login.html:58-63, 72-77`

**Implementation Steps:**
1. Add `tabindex="0"` to make icons focusable
2. Use `aria-describedby` pattern instead of tooltips
3. Create expandable help text section as alternative
4. Add keyboard event handlers (Space/Enter to show help)

**Dependencies:** None

---

### 30. Add ARIA Labels to Decorative Icons

**Status:** Pending
**Effort:** 1 hour
**Impact:** Low - Accessibility
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 3.3)

**Problem:**
Decorative icons announced by screen readers unnecessarily

**Files:**
- `src/stonks_overwatch/templates/login.html:68-76`
- `src/stonks_overwatch/templates/components/messages.html:5-12`

**Implementation Steps:**
1. Add `aria-hidden="true"` to all decorative icons
2. Ensure message text provides full context without icons
3. Add `role="alert"` to error message containers

**Dependencies:** None

---

### 31. Fix Password Toggle ARIA State

**Status:** Pending
**Effort:** 1 hour
**Impact:** Low - Accessibility
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 3.4)

**Problem:**
Password visibility button missing `aria-pressed` state

**Files:**
- `src/stonks_overwatch/templates/components/password_field.html:19-22`

**Implementation Steps:**
1. Add `aria-pressed="false"` to button element
2. Update JavaScript to toggle `aria-pressed` value
3. Update `base_broker_login.html:100-110` and `settings_content.html:383-394`
4. Keep the fixed icon toggle logic (remove/add instead of toggle)

**Dependencies:** None

---

### 32. Improve Mobile Responsiveness

**Status:** Pending
**Effort:** 2 hours
**Impact:** Low - Mobile UX
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 3.5)

**Problem:**
IBKR form too wide on mobile (650px on 375px viewport)

**Files:**
- `src/stonks_overwatch/templates/login/ibkr_login.html:9-11`

**Implementation Steps:**
1. Add responsive CSS media query for IBKR card
2. Reduce textarea rows on mobile (6 → 4 rows)
3. Test on iPhone SE (320px), iPhone 12 (390px), iPad (768px)

**Dependencies:** None

---

### 33. IBKR: Add Missing Timeout Configuration

**Status:** Pending
**Effort:** 1 hour
**Impact:** Low - Resilience
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 6.6)

**Problem:**
No timeout on external service calls

**Implementation Steps:**
1. Add timeout parameters to all external calls
2. Configure reasonable defaults (5-10 seconds)
3. Handle timeout exceptions gracefully

**Dependencies:** None

---

### 34. IBKR: Fix Logging Sensitive Data

**Status:** Pending
**Effort:** 0.5 hours
**Impact:** Low - Security hygiene
**Source:** BROKER_LOGIN_IMPROVEMENT_PLAN.md (Issue 6.7)

**Problem:**
Exception messages might contain credentials:

```python
self.logger.error(f"IBKR credentials validation error: {str(e)}")
```

**Files:**
- `src/stonks_overwatch/services/brokers/ibkr/services/authentication_service.py:105`

**Proposed Solution:**

```python
self.logger.error(f"IBKR credentials validation error: {type(e).__name__}")
```

**Implementation Steps:**
1. Log exception type instead of message
2. Sanitize error messages before logging
3. Add security audit logging

**Dependencies:** None

---

### 35. Configuration Management Enhancement

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

### 36. Logging Standardization

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

### 37. Performance Monitoring Dashboard

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

### 38. Enhanced Admin Interfaces

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

### Phase 1: Critical Security Fixes (Week 1) 🔴 BLOCKING

**MUST COMPLETE BEFORE PRODUCTION DEPLOYMENT**

- Remove plaintext credential storage (Task 1) - 4h
- Fix hardcoded portfolio values (Task 2) - 4h
- Add input validation (Task 3) - 3h
- Optimize authentication performance (Task 4) - 3h
- Implement session regeneration (Task 5) - 1h
- Extract IBKR retry logic (Task 13) - 2h

**Total: 17 hours**

---

### Phase 2: Code Quality Foundation (Weeks 2-3)

- Use BrokerFactory pattern (Task 8) - 1h
- Refactor authentication strategy (Task 9) - 4h
- Create ConfigurationManager (Task 10) - 3h
- Improve singleton architecture (Task 11) - 2h
- Complete remaining type hints (Task 12) - 1h *(60% complete)*
- Fix IBKR exception handling (Tasks 14, 16) - 2h
- Configure magic numbers (Task 17) - 1.5h

**Total: 14.5 hours**

---

### Phase 3: Testing & Service Layer (Weeks 4-5)

- Add view tests (Task 18) - 6h
- Add integration tests (Task 19) - 4h
- Parameterize test cases (Task 20) - 3h
- Fix currency detection (Task 21) - 2h
- Add price fetch safeguards (Task 22) - 2h
- Fix timezone handling (Task 23) - 1h
- Make cache TTL configurable (Task 24) - 1h
- Add IBKR type safety (Task 15) - 3h

**Total: 22 hours**

---

### Phase 4: Architecture Improvements (Weeks 6-8)

- Repository layer architecture (Task 6) - 2-3 days
- Complete database migration (Task 7) - 1-2 days
- Data transformation service (Task 25) - 3-4 days
- Complete cache migration (Task 26) - 2-3 days
- Jobs module refactoring (Task 27) - 4-5 days
- Middleware modernization (Task 28) - 3-4 days

**Total: ~15-21 days**

---

### Phase 5: UI/UX & Polish (Weeks 9-10)

- Fix keyboard navigation (Task 29) - 2h
- Add accessible tooltips (Task 30) - 3h
- Add ARIA labels (Task 31) - 1h
- Fix password toggle state (Task 32) - 1h
- Improve mobile responsiveness (Task 33) - 2h
- Add IBKR timeouts (Task 34) - 1h
- Fix logging sensitive data (Task 35) - 0.5h
- Configuration enhancement (Task 36) - 2-3 days
- Logging standardization (Task 37) - 2-3 days

**Total: ~10.5 hours + 4-6 days**

---

## Critical Path Summary

**Production Readiness Status:** ⚠️ **NOT READY**

**Blocking Issues (Must Fix):**
1. 🔴 Plaintext credentials in session (4h)
2. 🔴 Hardcoded portfolio values (4h)
3. 🟡 Missing input validation (3h)

**High Priority (Strongly Recommended):**
4. 🟡 Authentication performance (3h)
5. 🟡 IBKR duplicate retry logic (2h)
6. 🟡 Exception handling improvements (2h)

**Minimum Time to Production Ready:** 17 hours (critical path only)
**Recommended Time to Production Ready:** 31.5 hours (critical + high priority)

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

- Tasks are prioritized by impact on security, maintainability, and extensibility
- Effort estimates are approximate and may vary
- Dependencies should be completed before dependent tasks
- Some tasks can be done in parallel
- Phase 1 (Critical Security) is BLOCKING for production deployment

---

*Last Updated: January 12, 2026*
*Document Status: Active Planning*
*Source: Merged from BROKER_LOGIN_IMPROVEMENT_PLAN.md and existing PENDING_TASKS.md*
