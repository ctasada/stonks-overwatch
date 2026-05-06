# Authentication Operations Guide

> **Audience:** Developers, System Maintainers, DevOps Engineers
>
> **Purpose:** Operations, troubleshooting, monitoring, and maintenance guide for the authentication system.
>
> **Related Documentation:**
>
> - **[← Authentication Architecture](ARCHITECTURE_AUTHENTICATION.md)** - Technical design and flows
> - **[← Architecture Overview](ARCHITECTURE.md)** - System architecture
> - **[← Broker Integration Guide](ARCHITECTURE_BROKERS.md)** - Adding new brokers
> - **[Developer Guide](Developing-Stonks-Overwatch.md)** - Development setup
> - **[Configuration Guide](Configuration-Integration.md)** - Configuration details

---

## Table of Contents

- [Overview](#overview)
- [When to Use This Guide](#when-to-use-this-guide)
- [Prerequisites](#prerequisites)
- [Troubleshooting Workflow](#troubleshooting-workflow)
- [Quick Reference](#quick-reference)
- [Quick Diagnostic](#quick-diagnostic)
- [Common Maintenance Tasks](#common-maintenance-tasks)
- [Architecture Summary](#architecture-summary)
- [Security Checklist](#security-checklist)
- [Integration Reference](#integration-reference)
- [Emergency Procedures](#emergency-procedures)
- [Appendix](#appendix)

---

## Overview

Use this guide to maintain and troubleshoot the Stonks Overwatch authentication system. Whether you're investigating a production issue, implementing monitoring, or performing routine maintenance, you'll find the procedures and diagnostic commands you need.

### Why These Features Matter to You

**Service Architecture** (Factory pattern + dependency injection)
→ Makes testing easier: Mock services without touching production code

**Error Handling** (Structured exceptions)
→ Speeds debugging: Clear error hierarchies show exactly what failed

**Performance** (Service locator caching)
→ Reduces latency: >90% faster after initial service creation

**Type Safety** (Interface contracts)
→ Catches errors early: Integration issues fail at development time, not runtime

**Security** (Credential masking)
→ Prevents leaks: Sensitive data automatically filtered from logs

### Architecture Updates

Recent improvements to the authentication system:

- ✅ **Unified Factory Pattern**: Centralized service creation with automatic dependency injection
- ✅ **Service Locator**: High-performance cached access to authentication services
- ✅ **Interface-Based Design**: Type-safe contracts for all authentication operations
- ✅ **Enhanced In-App Auth**: Complete support for DEGIRO In-App authentication flow
- ✅ **Professional Error Handling**: Structured exception hierarchy with recovery strategies

For architectural details, see [Authentication Architecture](ARCHITECTURE_AUTHENTICATION.md).

---

## When to Use This Guide

**Use this guide when:**

- ✅ Debugging authentication failures in production
- ✅ Investigating user login issues
- ✅ Implementing authentication monitoring
- ✅ Understanding session state management
- ✅ Troubleshooting TOTP or In-App auth flows
- ✅ Performing system maintenance on auth components

**Refer to other docs for:**

- ❌ Initial setup → [Quickstart Guide](Quickstart.md)
- ❌ Architecture design → [Authentication Architecture](ARCHITECTURE_AUTHENTICATION.md)
- ❌ Adding brokers → [Broker Integration Guide](ARCHITECTURE_BROKERS.md)
- ❌ User configuration → [DEGIRO Setup](DEGIRO.md)

---

## Prerequisites

### Required Knowledge

- Python development experience
- Django framework basics
- Understanding of HTTP sessions
- Basic SQL knowledge (for database operations)

### Required Access

- Access to application logs (`data/logs/stonks-overwatch.log`)
- Django shell access for debugging
- Database access (SQLite or configured database)
- Application source code

### Recommended Reading

Before using this guide, familiarize yourself with:

1. [Authentication Architecture](ARCHITECTURE_AUTHENTICATION.md) - Understanding the system design
2. [Architecture Overview](ARCHITECTURE.md) - Core system patterns
3. [Developing Stonks Overwatch](Developing-Stonks-Overwatch.md) - Development environment setup
4. [Configuration Integration](Configuration-Integration.md) - Configuration system

---

## Troubleshooting Workflow

Follow this systematic approach when debugging authentication issues:

1. **Identify symptoms** → Check [Common Issues](#2-troubleshooting-common-issues) for known problems
2. **Gather data** → Run [diagnostic commands](#1-debugging-authentication-issues) to collect information
3. **Enable logging** → Turn on [debug logging](#enable-debug-logging) for detailed diagnostics
4. **Analyze logs** → Search for [key log markers](#key-log-markers) in application logs
5. **Test fixes** → Use [testing procedures](#6-testing-authentication) to verify solutions
6. **Verify** → Confirm issue resolved with [performance monitoring](#7-performance-monitoring)

**Still stuck?** → [Emergency Procedures](#emergency-procedures)

---

## Quick Reference

### 🚀 Start Here

**Most common task**—Get authentication service in any context:

```python
from stonks_overwatch.core.authentication_locator import get_authentication_service

# In views, middleware, or shell
auth_service = get_authentication_service()

# For testing, you'll also need a request
from django.test import RequestFactory
factory = RequestFactory()
request = factory.get('/')
```

**Copy this** into Django shell, views, middleware, or tests.

### 📁 File Quick Reference

Find these files when debugging specific issues:

**Login failing?** → `src/stonks_overwatch/services/utilities/authentication_service.py`
**Session lost?** → `src/stonks_overwatch/services/utilities/authentication_session_manager.py`
**Credentials wrong?** → `src/stonks_overwatch/services/utilities/authentication_credential_service.py`

[See complete file list below](#key-files)

### Key Files

| Component | Location | Purpose | When to Check |
|-----------|----------|---------|---------------|
| **Main Service** | `src/stonks_overwatch/services/utilities/authentication_service.py` | Core authentication orchestration | Auth flow issues, login failures |
| **Session Manager** | `src/stonks_overwatch/services/utilities/authentication_session_manager.py` | Session state management | Lost credentials, session expires |
| **Credential Service** | `src/stonks_overwatch/services/utilities/authentication_credential_service.py` | Credential handling | "Remember me" fails, config issues |
| **Service Locator** | `src/stonks_overwatch/core/authentication_locator.py` | Optimized service access | Performance problems, caching |
| **Factory** | `src/stonks_overwatch/core/factories/authentication_factory.py` | Service creation | Initialization errors |
| **Middleware** | `src/stonks_overwatch/middleware/degiro_auth.py` | Route protection | Redirect loops, access denied |
| **Login View** | `src/stonks_overwatch/views/login.py` | User interface | UI issues, form problems |

### Common Patterns

**Service Locator Pattern** (recommended for most cases):

```python
from stonks_overwatch.core.authentication_locator import get_authentication_service

auth_service = get_authentication_service()  # Uses cached instance
```

**Session State Management**:

```python
# Always use the session manager for state
session_manager = auth_service.session_manager

# Set state
session_manager.set_authenticated(request, True)
session_manager.set_totp_required(request, False)

# Get state
is_auth = session_manager.is_authenticated(request)
needs_totp = session_manager.is_totp_required(request)

# Clear state
session_manager.clear_session(request)
```

---

## Quick Diagnostic

### 5-Minute Health Check

Run this to verify authentication system health:

```python
# Copy-paste into Django shell
from stonks_overwatch.core.authentication_locator import AuthenticationServiceLocator
from django.test import RequestFactory

print("=== Authentication System Health Check ===\n")

# Check service registration and caching
status = AuthenticationServiceLocator.get_cache_status()
print(f"✅ Services registered: {status['factory_services_registered']}")
print(f"✅ Service cached: {status['auth_service_cached']}")
print(f"✅ Factory cached: {status['factory_cached']}")
print(f"📊 Access count: {status['access_count']}")

# Check basic auth flow
print("\n=== Testing Basic Flow ===\n")
factory = RequestFactory()
request = factory.get('/')
auth_service = AuthenticationServiceLocator.get_authentication_service()

try:
    # Test service access
    is_auth = auth_service.is_user_authenticated(request)
    print(f"✅ Service accessible: Authentication check returned {is_auth}")

    # Test session manager
    session_data = auth_service.session_manager.get_session_data(request)
    print(f"✅ Session manager working: Retrieved session data")

    # Test credential service
    has_db = auth_service.credential_service.get_credentials_from_database() is not None
    print(f"📝 Database credentials: {'Found' if has_db else 'Not configured'}")

    print("\n✅ System Healthy - All checks passed")

except Exception as e:
    print(f"\n❌ System Issue Detected: {str(e)}")
    print("→ See [Common Issues](#2-troubleshooting-common-issues) for solutions")
```

**Expected Results:**

- ✅ **Green checkmarks** = System healthy
- ❌ **Red X** = See [Troubleshooting](#common-maintenance-tasks) below

### Broker Readiness Check

Use this to quickly check if brokers are ready for authentication:

```python
# Copy-paste into Django shell
from stonks_overwatch.core.authentication_helper import AuthenticationHelper
from stonks_overwatch.constants import BrokerName
from django.test import RequestFactory

print("=== Broker Readiness Check ===\n")

# Check specific brokers
for broker in [BrokerName.DEGIRO, BrokerName.BITVAVO, BrokerName.IBKR]:
    is_ready = AuthenticationHelper.is_broker_ready(broker)
    status = "✅ Ready" if is_ready else "❌ Not Ready"
    print(f"{broker.display_name}: {status}")

# Find first ready broker (useful for auto-authentication)
ready_broker = AuthenticationHelper.get_first_ready_broker()
if ready_broker:
    print(f"\n🎯 First ready broker: {ready_broker.display_name}")
else:
    print("\n⚠️  No brokers ready - check configuration")

# Check if any brokers configured
factory = RequestFactory()
request = factory.get('/')
has_any = AuthenticationHelper.has_configured_brokers(request)
print(f"\n📋 Has configured brokers: {has_any}")
```

**Expected Output:**

```text
=== Broker Readiness Check ===

DEGIRO: ✅ Ready
Bitvavo: ✅ Ready
Interactive Brokers: ❌ Not Ready

🎯 First ready broker: DEGIRO

📋 Has configured brokers: True
```

**If all brokers show "Not Ready":**

1. Check database credentials with `get_credentials_from_database()`
2. Verify configuration files have valid credentials
3. Ensure brokers are enabled in settings

---

## Common Maintenance Tasks

**Choose your starting point:**

- 🔍 **Login not working?** → [Debugging Authentication Issues](#1-debugging-authentication-issues)
- 📋 **Seen this error before?** → [Troubleshooting Common Issues](#2-troubleshooting-common-issues)
- 📱 **In-App auth stuck?** → [In-App Authentication Debugging](#3-in-app-authentication-debugging)
- ⚙️ **Changing config?** → [Configuration Management](#4-configuration-management)
- 📊 **Need visibility?** → [Monitoring and Logging](#5-monitoring-and-logging)
- 🧪 **Testing changes?** → [Testing Authentication](#6-testing-authentication)
- 🚀 **System slow?** → [Performance Monitoring](#7-performance-monitoring)

### 1. Debugging Authentication Issues

#### Verify Authentication Status

```python
# Context: Use in Django shell or debug context
from stonks_overwatch.core.authentication_locator import get_authentication_service
from django.http import HttpRequest

auth_service = get_authentication_service()
status = auth_service.get_authentication_status(request)
print(status)

# Expected output when authenticated:
# {
#   'is_authenticated': True,
#   'session_id': 'abc12***',
#   'username': 'user@example.com',
#   'totp_required': False
# }
```

#### Inspect Session Data

```python
session_data = auth_service.session_manager.get_session_data(request)
print(f"Authenticated: {session_data.get('is_authenticated')}")
print(f"TOTP Required: {session_data.get('totp_required')}")
print(f"Session ID: {session_data.get('session_id')}")  # Partially masked for security
print(f"Credentials: {session_data.get('credentials')}")  # Password masked
```

#### Identify Credential Sources

```python
has_session, has_database, has_config = auth_service.credential_service.get_credential_sources(request)
print(f"Has session credentials: {has_session}")
print(f"Has database credentials: {has_database}")
print(f"Has config credentials: {has_config}")

# Expected: At least one should be True for authentication to work
```

#### Clear Broken Authentication State

```python
# Context: Use when session exists but config is invalid
from stonks_overwatch.core.authentication_helper import AuthenticationHelper
from stonks_overwatch.constants import BrokerName

# Clear broken session for specific broker
AuthenticationHelper.clear_broken_session(request, BrokerName.DEGIRO)
print("✅ Cleared broken session data for DEGIRO")

# Verify session cleared
is_auth = auth_service.session_manager.is_authenticated(request)
print(f"Authentication status after clear: {is_auth}")  # Should be False
```

**When to use this:**

- User sees "Session exists but configuration is invalid" error
- Authentication loops infinitely
- Session data is corrupted or inconsistent

**If issues persist:**

1. Check [Common Issues](#2-troubleshooting-common-issues) for known problems
2. Enable [debug logging](#enable-debug-logging) for detailed diagnostics
3. Review [emergency procedures](#emergency-procedures) if system is unrecoverable
4. Contact maintainers via [CONTRIBUTING.md](../CONTRIBUTING.md)

---

### 2. Troubleshooting Common Issues

#### TOTP Credentials Lost

**Symptoms**: "Username and password required" during two-factor authentication
**Solution**: Check if `store_credentials()` is called in `check_broker_connection()`
**Related**: See [Session State Management](#common-patterns)

```python
# Verify credentials are stored during TOTP flow
auth_service.session_manager.store_credentials(
    request=request,
    username=username,
    password=password,
    remember_me=remember_me
)
```

---

#### Session Cleared Unexpectedly

**Symptoms**: User logged out after entering TOTP code
**Solution**: Verify `preserve_session=True` for TOTP in middleware
**Related**: See [Middleware Integration](#middleware-integration)

```python
# In middleware, ensure session preservation during TOTP
if totp_required:
    return redirect_to_totp_form(preserve_session=True)
```

---

#### Login Form Not Showing Two-Factor Authentication

**Symptoms**: Username/password form shown instead of TOTP input
**Solution**: Check if `set_totp_required(request, True)` is called
**Related**: See [Authentication Architecture](ARCHITECTURE_AUTHENTICATION.md#totp-2fa-flow)

```python
# After initial auth attempt detects TOTP needed
auth_service.session_manager.set_totp_required(request, True)
```

---

#### Remember Me Not Working

**Symptoms**: Credentials not saved in database
**Solution**: Verify `store_credentials_in_database()` is called after successful auth
**Related**: See [Configuration Management](#4-configuration-management)

```python
# After successful authentication with remember_me=True
if remember_me:
    auth_service.credential_service.store_credentials_in_database(username, password)
```

---

#### In-App Authentication Not Triggered

**Symptoms**: Username/password form instead of "Open DEGIRO app"
**Solution**: Check if `set_in_app_auth_required(request, True)` is called
**Related**: See [In-App Authentication Debugging](#3-in-app-authentication-debugging)

```python
# When DEGIRO returns in-app auth required
auth_service.session_manager.set_in_app_auth_required(request, True)
```

---

#### In-App Waiting Loop Stuck

**Symptoms**: Spinner shows indefinitely
**Solution**: Check DEGIRO mobile app for notification; verify token stored in session
**Debugging**: Enable debug logging to see polling attempts

```python
# Check if token exists
credentials = auth_service.session_manager.get_credentials(request)
has_token = bool(credentials and credentials.in_app_token)
print(f"Has in-app token: {has_token}")
```

---

#### In-App Token Missing

**Symptoms**: "No in-app token found" error
**Solution**: Verify `in_app_token` is stored during `store_credentials()` call
**Related**: See [In-App Authentication Debugging](#3-in-app-authentication-debugging)

---

#### In-App Authentication Clearing Unexpectedly

**Symptoms**: Back to login form during wait
**Solution**: Check error handling in `_wait_for_in_app_confirmation()`
**Debugging**: Review logs for exception messages

📝 **Note**: This table reflects commonly observed issues. For your specific case, enable debug logging to get detailed diagnostics.

---

### 3. In-App Authentication Debugging

#### Check In-App Authentication Status

```python
# Context: Use to verify In-App auth state
from stonks_overwatch.core.authentication_locator import get_authentication_service

auth_service = get_authentication_service()
in_app_required = auth_service.session_manager.is_in_app_auth_required(request)
print(f"In-App auth required: {in_app_required}")

# Expected: True if waiting for mobile app confirmation
```

#### Check In-App Token in Session

```python
# Context: Verify token was stored from DEGIRO API response
credentials = auth_service.session_manager.get_credentials(request)
has_token = bool(credentials and credentials.in_app_token)
print(f"Has in-app token: {has_token}")

if credentials and credentials.in_app_token:
    # Show preview (first 8 chars for security)
    print(f"Token preview: {credentials.in_app_token[:8]}...")
```

#### Debug In-App Waiting Loop

```python
# Context: Monitor waiting loop status (add to authentication service for debugging)
from time import sleep
from degiro_connector.core.exceptions import DeGiroConnectionError

self.logger.info(f"Starting in-app wait for user: {credentials.username}")
self.logger.info(f"Token preview: {credentials.in_app_token[:8]}...")

# In _wait_for_in_app_confirmation method
max_attempts = 60  # 5 minutes at 5-second intervals
attempts = 0

while attempts < max_attempts:
    sleep(5)
    attempts += 1

    try:
        trading_api.connect()
        self.logger.info("In-app authentication successful")
        return True
    except DeGiroConnectionError as retry_error:
        status = retry_error.error_details.status
        self.logger.debug(f"Retry #{attempts}, status: {status}")

        if status == 3:  # Still waiting for user
            self.logger.debug("Still waiting for user confirmation...")
            continue
        else:
            # Unrecoverable error
            raise retry_error
```

#### Test In-App Flow Manually

Step 1: Create test request and service

```python
# Context: Django shell - simulate In-App authentication
from django.test import RequestFactory
from stonks_overwatch.core.authentication_locator import get_authentication_service

factory = RequestFactory()
request = factory.post('/login')
auth_service = get_authentication_service()
```

Step 2: Store credentials with In-App token

```python
# Store test credentials (use realistic formats)
auth_service.session_manager.store_credentials(
    request=request,
    username='john.doe@example.com',  # Realistic email format
    password='SecureP@ssw0rd',         # Example password format
    in_app_token='1a2b3c4d5e6f7g8h',   # 16-char hex token
    remember_me=False
)
```

Step 3: Set flag and test authentication

```python
# Set In-App required flag
auth_service.session_manager.set_in_app_auth_required(request, True)

# Test in-app authentication handling (service layer)
result = auth_service.handle_in_app_authentication(request)
print(f"Result: {result.result}")
print(f"Message: {result.message}")
print(f"Session ID: {result.session_id}")

# Expected successful output:
# Result: SUCCESS
# Message: Authentication successful
# Session ID: abc123***
```

**If issues persist:**

1. Verify DEGIRO mobile app is up to date
2. Check network connectivity to DEGIRO API
3. Review [Authentication Architecture](ARCHITECTURE_AUTHENTICATION.md#in-app-authentication) for flow details

---

### 4. Configuration Management

#### Check Broker Configuration

```python
from stonks_overwatch.services.brokers.models import BrokersConfigurationRepository

config = BrokersConfigurationRepository.get_broker_by_name("degiro")
print(f"Enabled: {config.is_enabled}")
print(f"Has credentials: {'username' in config.credentials}")

# Expected: is_enabled=True, credentials should have username key
```

#### Update Credentials Programmatically

```python
from stonks_overwatch.config.degiro import DegiroCredentials

creds = DegiroCredentials(username="user@example.com", password="pass", remember_me=True)
auth_service.credential_service.store_credentials_in_database(creds.username, creds.password)

# Verify storage
stored = auth_service.credential_service.get_credentials_from_database()
print(f"Credentials stored: {stored is not None}")
```

---

### 5. Monitoring and Logging

#### Enable Debug Logging

Add this configuration to your Django settings file (`settings.py`):

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'stonks_overwatch.auth_service': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'stonks_overwatch.core': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

#### Key Log Markers

Search application logs for these markers:

- **`[AUTH|SERVICE]`**: Main authentication operations (including In-App auth processing)
- **`[AUTH|SESSION_MANAGER]`**: Session state changes
- **`[AUTH|CREDENTIAL_SERVICE]`**: Credential operations
- **`[DEGIRO|AUTH_MIDDLEWARE]`**: Middleware authentication checks
- **`[VIEW|LOGIN]`**: Login view UI operations
- **`[AUTH_LOCATOR]`**: Service locator operations

#### Important Log Messages

- `"TOTP required during connection check"`: Two-factor authentication flow initiated
- `"In-app authentication required during connection check"`: In-App flow initiated
- `"Stored credentials in session"`: Credentials cached for TOTP/In-App
- `"Handling in-app authentication"`: In-App auth delegated to service layer
- `"Starting in-app authentication for user"`: In-App waiting loop started
- `"Starting in-app authentication wait loop for token"`: Polling begins
- `"Still waiting for in-app confirmation"`: User hasn't confirmed yet
- `"In-app authentication successful"`: Mobile app confirmation received
- `"User logged out successfully"`: Complete logout
- `"Authentication failed"`: General auth failure

#### Log File Locations

- **Development**: Console output (stdout)
- **Production**: `data/logs/stonks-overwatch.log`
- **Native App (macOS)**: `~/Library/Logs/com.caribay.stonks_overwatch/`
- **Native App (Windows)**: `%LOCALAPPDATA%\Stonks Overwatch\Logs\`
- **Native App (Linux)**: `~/.local/share/stonks-overwatch/logs/`

---

### 6. Testing Authentication

#### Test Standard Authentication Flow

```python
# Context: Django shell - test basic username/password auth
from django.test import RequestFactory
from stonks_overwatch.core.authentication_locator import get_authentication_service

factory = RequestFactory()
request = factory.post('/login', {'username': 'test', 'password': 'test'})

auth_service = get_authentication_service()
result = auth_service.authenticate_user(request, 'username', 'password', None, False)

print(f"Result: {result.result}")
print(f"Message: {result.message}")

# Expected successful output:
# Result: SUCCESS
# Message: Authentication successful
```

#### Test In-App Authentication Flow

See [In-App Authentication Debugging](#3-in-app-authentication-debugging) for complete test procedure.

💡 **Tip**: These examples are for illustration. Adapt them to your specific testing environment and ensure proper setup of request sessions.

---

### 7. Performance Monitoring

#### Check Service Locator Performance

```python
from stonks_overwatch.core.authentication_locator import AuthenticationServiceLocator

# Get cache status for performance analysis
status = AuthenticationServiceLocator.get_cache_status()
print(f"Access count: {status['access_count']}")
print(f"Factory cached: {status['factory_cached']}")
print(f"Auth service cached: {status['auth_service_cached']}")
print(f"Services registered: {status['factory_services_registered']}")
```

#### Performance Benchmarks

Typical performance on standard hardware (development environment):

| Operation | First Access | Cached Access | Target |
|-----------|--------------|---------------|--------|
| Service creation | ~50ms | <1ms | <100ms |
| Auth check | ~100ms | ~10ms | <200ms |
| Session read | ~5ms | ~1ms | <10ms |

**If you see worse performance**, check:

1. Database connection latency
2. Session backend configuration (Redis vs database)
3. Cache status and memory pressure
4. Network latency to DEGIRO API (for remote auth)

#### Performance Considerations

- **First Access**: May take longer due to service initialization (~50-100ms)
- **Subsequent Access**: Should use cached instances (<1ms)
- **Memory Impact**: Cached services remain in memory until cleared (~5-10MB)
- **Cache Clearing**: Call `AuthenticationServiceLocator.clear_cache()` to free memory

**Next steps for performance issues:**

1. Review [Architecture Summary](#architecture-summary) to understand caching strategy
2. Check database query performance with Django Debug Toolbar
3. Monitor memory usage with system tools
4. Consider upgrading session backend to Redis for better performance

---

## Architecture Summary

The authentication system follows a layered architecture:

- **Presentation Layer**: Login views, middleware
- **Service Layer**: Authentication services, session management, credential handling
- **Infrastructure**: Factory pattern with service locator for performance
- **Data Layer**: Django sessions, database, configuration files

**Component Responsibilities:**

| Layer | Components | Purpose |
|-------|------------|---------|
| **Presentation** | Login View, Middleware | User interface, route protection |
| **Service** | AuthService, SessionManager, CredentialService | Business logic, state management |
| **Infrastructure** | Factory, Service Locator | Service creation, caching |
| **Data** | Session, Database, Config | State persistence |

**Key Patterns:**

- **Factory Pattern**: Centralized service creation with dependency injection
- **Service Locator**: High-performance cached access to services
- **Interface Contracts**: Type-safe service boundaries

> **📖 Detailed Architecture**: See [Authentication Architecture](ARCHITECTURE_AUTHENTICATION.md) for complete diagrams, flows, and design decisions.

---

## Security Checklist

### Credential Protection

Review these security measures:

- 🔒 **Passwords never logged in plain text** - Enforced by masked logging
- 🔒 **Session credentials cleared on logout** - Automatic cleanup
- 🔒 **Database credentials encrypted** - BrokersConfiguration model
- 🔒 **TOTP codes not persisted** - Memory only, never stored
- 🔒 **Session IDs partially masked in logs** - Privacy protection

### Error Handling

Verify error handling security:

- 🔒 **Error messages don't expose sensitive data** - Structured error classes
- 🔒 **Authentication failures logged with context** - Audit trail without credentials
- 🔒 **Exception handling follows proper hierarchy** - No information leakage

### Architecture Security

Confirm architectural security:

- 🔒 **Service interfaces prevent unauthorized access** - Type-safe contracts
- 🔒 **Dependency injection maintains secure boundaries** - Service isolation
- 🔒 **Cache status doesn't expose sensitive information** - Sanitized output only

---

## Integration Reference

### Middleware Integration

- **File**: `src/stonks_overwatch/middleware/degiro_auth.py`
- **Purpose**: Protects routes, handles TOTP redirects
- **Key Method**: `_check_authentication()`
- **Documentation**: See [Authentication Architecture](ARCHITECTURE_AUTHENTICATION.md#connection-check-flow-middleware)

### Login View Integration

- **File**: `src/stonks_overwatch/views/login.py`
- **Purpose**: Handles user login UI, delegates authentication to service layer
- **Key Methods**:
  - `_perform_authentication()`: Delegates to AuthenticationService
  - `_handle_in_app_authentication()`: Delegates to AuthenticationService.handle_in_app_authentication()

### Authentication Service Integration

- **File**: `src/stonks_overwatch/services/utilities/authentication_service.py`
- **Purpose**: Core authentication logic including In-App authentication processing
- **Key Methods**:
  - `authenticate_user()`: Main authentication orchestration
  - `handle_totp_authentication()`: TOTP processing
  - `handle_in_app_authentication()`: In-App authentication orchestration
  - `_wait_for_in_app_confirmation()`: In-App polling loop (uses DEGIRO Service)

### DEGIRO Service Integration

- **File**: `src/stonks_overwatch/services/brokers/degiro/client/degiro_client.py`
- **Purpose**: API connectivity, credential validation
- **Key Method**: `check_connection()`

---

## Emergency Procedures

🚨 **Danger Zone**: These procedures are for emergency recovery only. They can cause data loss or system downtime.

**Before proceeding:**

1. ✅ Back up your database
2. ✅ Notify affected users
3. ✅ Have rollback plan ready
4. ✅ Test in staging environment first

### Reset Authentication State

```python
# Clear all session data (non-destructive)
auth_service.session_manager.clear_session(request)

# Force logout
auth_service.logout_user(request)

# Clear stored credentials from memory
auth_service.credential_service.clear_stored_credentials()
```

### Bypass Authentication (Development Only)

⚠️ **Warning**: Only use in development environments. **Never use in production.**

```python
# DEVELOPMENT ONLY - Manually set authenticated state
auth_service.session_manager.set_authenticated(request, True)
auth_service.session_manager.set_session_id(request, "dev_session_12345")
```

### Database Credential Recovery

⚠️ **Warning**: Always backup database before running these commands.

```bash
# Step 1: Backup database first (REQUIRED)
cp data/db.sqlite3 data/db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)
ls -lh data/db.sqlite3.backup.*  # Verify backup created
```

```sql
-- Step 2: Check stored credentials
SELECT broker_name, is_enabled, credentials
FROM stonks_overwatch_brokersconfiguration
WHERE broker_name = 'degiro';

-- Step 3: DANGER - Clear stored credentials if corrupted
-- This will log out all users and require re-authentication
UPDATE stonks_overwatch_brokersconfiguration
SET credentials = '{}'
WHERE broker_name = 'degiro';
```

⚠️ **Important**: After clearing credentials, users must log in again. Consider notifying users before performing this operation.

### Rollback Emergency Changes

If emergency procedure caused issues:

```bash
# Step 1: Stop application first
# For systemd:
systemctl stop stonks-overwatch

# Or for development:
# Press Ctrl+C to stop runserver

# Step 2: Restore database from backup
cp data/db.sqlite3.backup.YYYYMMDD_HHMMSS data/db.sqlite3

# Verify restoration
ls -lh data/db.sqlite3

# Step 3: Restart application
systemctl start stonks-overwatch

# Or for development:
# make run

# Step 4: Verify restoration successful
python manage.py shell
# Run Quick Diagnostic from above
```

---

## Appendix

### Adding New Authentication Check

Template for implementing new authentication checks:

```python
def new_auth_check(self, request):
    """
    Template for new authentication checks.

    Args:
        request: The HTTP request object

    Returns:
        AuthenticationResponse with result status
    """
    try:
        # Step 1: Check if authentication is needed
        if not self.should_perform_check():
            return self._create_success_response("Check skipped")

        # Step 2: Perform the check
        result = self.perform_check(request)

        # Step 3: Handle errors appropriately
        if result.has_error:
            return self._create_error_response(result.error_type, result.message)

        # Step 4: Return success
        return self._create_success_response("Check completed")

    except Exception as e:
        self.logger.error(f"Error in new auth check: {str(e)}")
        return self._create_error_response(
            AuthenticationResult.CONNECTION_ERROR,
            str(e)
        )
```

### Glossary

- **Service Locator**: Centralized registry that provides cached access to services, eliminating repeated initialization overhead
- **Dependency Injection**: Design pattern where dependencies are provided to objects rather than created internally
- **TOTP**: Time-based One-Time Password, a form of two-factor authentication
- **In-App Authentication**: DEGIRO's mobile app confirmation system for login requests
- **Session Manager**: Component responsible for managing authentication state across requests
- **Credential Service**: Component that handles credential storage, retrieval, and validation

---

---

## Additional Resources

### Related Documentation

- **[Authentication Architecture](ARCHITECTURE_AUTHENTICATION.md)** - Complete technical design and flows
- **[Architecture Overview](ARCHITECTURE.md)** - System-wide architecture patterns
- **[Broker Integration Guide](ARCHITECTURE_BROKERS.md)** - Adding new broker integrations
- **[Pending Tasks](PENDING_TASKS.md)** - Known issues and improvements

### Support

- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Join GitHub Discussions for questions
- **Contributing**: See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines

---

*Last Updated: November 2025*
*Document Type: Operations Guide*
