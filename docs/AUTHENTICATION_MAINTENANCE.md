# Authentication System Maintenance Guide

## Recent Architecture Updates (2025)

✅ **Modern Service Architecture**: Unified factory pattern with dependency injection
✅ **Professional Error Handling**: Comprehensive exception hierarchy and recovery
✅ **Performance Optimizations**: Service locator with intelligent caching
✅ **Interface-Based Design**: Type-safe contracts and abstractions
✅ **Enhanced Security**: Proper credential masking and session management

## Quick Reference

### Service Access

```python
from stonks_overwatch.core.authentication_locator import get_authentication_service
auth_service = get_authentication_service()
```

### Key Files

- **Main Service**: `src/stonks_overwatch/services/utilities/authentication_service.py`
- **Session Manager**: `src/stonks_overwatch/services/utilities/authentication_session_manager.py`
- **Credential Service**: `src/stonks_overwatch/services/utilities/authentication_credential_service.py`
- **Middleware**: `src/stonks_overwatch/middleware/degiro_auth.py`
- **Login View**: `src/stonks_overwatch/views/login.py`

## Common Maintenance Tasks

### 1. Debugging Authentication Issues

**Check authentication status:**

```python
# In Django shell or debug
auth_service = get_authentication_service()
status = auth_service.get_authentication_status(request)
print(status)  # Shows complete auth state
```

**Check session data:**

```python
session_data = auth_service.session_manager.get_session_data(request)
print(f"Authenticated: {session_data.get('is_authenticated')}")
print(f"TOTP Required: {session_data.get('totp_required')}")
print(f"Session ID: {session_data.get('session_id')}")  # Partially masked for security
print(f"Credentials: {session_data.get('credentials')}")  # Password masked
```

**Check credential sources:**

```python
has_session, has_database, has_config = auth_service.credential_service.get_credential_sources(request)
print(f"Has session credentials: {has_session}")
print(f"Has database credentials: {has_database}")
print(f"Has config credentials: {has_config}")
```

### 2. Common Issues and Solutions

| Issue | Symptoms | Solution |
|-------|----------|----------|
| **TOTP credentials lost** | "Username and password required" during 2FA | Check if `store_credentials()` is called in `check_degiro_connection()` |
| **Session cleared unexpectedly** | User logged out after TOTP | Verify `preserve_session=True` for TOTP in middleware |
| **Login form not showing 2FA** | Username/password form shown instead of TOTP | Check if `set_totp_required(request, True)` is called |
| **Remember me not working** | Credentials not saved in database | Verify `store_credentials_in_database()` is called after successful auth |
| **In-App auth not triggered** | Username/password form instead of "Open DEGIRO app" | Check if `set_in_app_auth_required(request, True)` is called |
| **In-App waiting loop stuck** | Spinner shows indefinitely | Check DEGIRO mobile app for notification; verify token stored in session |
| **In-App token missing** | "No in-app token found" error | Verify `in_app_token` is stored during `store_credentials()` call |
| **In-App auth clearing unexpectedly** | Back to login form during wait | Check error handling in `_wait_for_in_app_confirmation()` |

### 2.1. In-App Authentication Debugging (New 2025)

**Check In-App authentication status:**

```python
# Check if In-App auth is required
auth_service = get_authentication_service()
in_app_required = auth_service.session_manager.is_in_app_auth_required(request)
print(f"In-App auth required: {in_app_required}")
```

**Check In-App token in session:**

```python
# Check stored credentials include in_app_token
credentials = auth_service.session_manager.get_credentials(request)
has_token = bool(credentials and credentials.in_app_token)
print(f"Has in-app token: {has_token}")
if credentials and credentials.in_app_token:
    print(f"Token preview: {credentials.in_app_token[:8]}...")
```

**Debug In-App waiting loop:**

```python
# Monitor waiting loop status (add to login view for debugging)
self.logger.info(f"Starting in-app wait for user: {credentials.username}")
self.logger.info(f"Token: {credentials.in_app_token[:8]}...")

# In _wait_for_in_app_confirmation method
while True:
    sleep(5)
    try:
        trading_api.connect()
        self.logger.info("In-app authentication successful")
        return True
    except DeGiroConnectionError as retry_error:
        self.logger.debug(f"Retry error status: {retry_error.error_details.status}")
        if retry_error.error_details.status == 3:
            self.logger.debug("Still waiting for user confirmation...")
            continue
```

**Test In-App flow manually:**

```python
# In Django shell - simulate In-App authentication
from django.test import RequestFactory
from stonks_overwatch.core.authentication_locator import get_authentication_service

factory = RequestFactory()
request = factory.post('/login')

auth_service = get_authentication_service()

# Store test credentials with in_app_token
auth_service.session_manager.store_credentials(
    request=request,
    username='test_user',
    password='test_pass',
    in_app_token='test_token_12345',
    remember_me=False
)

# Set In-App required flag
auth_service.session_manager.set_in_app_auth_required(request, True)

# Check session state
session_data = auth_service.session_manager.get_session_data(request)
print(f"Session data: {session_data}")
```

### 3. Configuration Management

**Check broker configuration:**

```python
from stonks_overwatch.services.brokers.models import BrokersConfigurationRepository
config = BrokersConfigurationRepository.get_broker_by_name("degiro")
print(f"Enabled: {config.is_enabled}")
print(f"Has credentials: {'username' in config.credentials}")
```

**Update credentials programmatically:**

```python
from stonks_overwatch.config.degiro import DegiroCredentials
creds = DegiroCredentials(username="user", password="pass", remember_me=True)
auth_service.credential_service.store_credentials_in_database(creds.username, creds.password)
```

### 4. Monitoring and Logging

**Key log markers to search for:**
- `[AUTH|SERVICE]`: Main authentication operations (including In-App auth processing)
- `[AUTH|SESSION_MANAGER]`: Session state changes
- `[AUTH|CREDENTIAL_SERVICE]`: Credential operations
- `[DEGIRO|AUTH_MIDDLEWARE]`: Middleware authentication checks
- `[VIEW|LOGIN]`: Login view UI operations (In-App auth UI delegation only)

**Important log messages:**
- `"TOTP required during connection check"`: TOTP flow initiated
- `"In-app authentication required during connection check"`: In-App flow initiated
- `"Stored credentials in session"`: Credentials cached for TOTP/In-App
- `"Handling in-app authentication"`: In-App auth delegated to service layer
- `"Starting in-app authentication for user"`: In-App waiting loop started (service layer)
- `"Starting in-app authentication wait loop for token"`: Polling begins (service layer)
- `"Still waiting for in-app confirmation"`: User hasn't confirmed yet
- `"In-app authentication successful"`: Mobile app confirmation received (service layer)
- `"User logged out successfully"`: Complete logout
- `"Authentication failed"`: General auth failure

### 5. Testing Authentication Locally

**Test standard authentication flow:**

```python
# In Django shell
from django.test import RequestFactory
from stonks_overwatch.core.authentication_locator import get_authentication_service

factory = RequestFactory()
request = factory.post('/login', {'username': 'test', 'password': 'test'})

auth_service = get_authentication_service()
result = auth_service.authenticate_user(request, 'username', 'password', None, False)
print(f"Result: {result.result}")
print(f"Message: {result.message}")
```

**Test in-app authentication flow:**

```python
# In Django shell - test in-app authentication service method
from django.test import RequestFactory
from stonks_overwatch.core.authentication_locator import get_authentication_service
from stonks_overwatch.config.degiro import DegiroCredentials

factory = RequestFactory()
request = factory.post('/login')

# Set up session with in-app credentials (normally done by initial auth)
auth_service = get_authentication_service()
auth_service.session_manager.store_credentials(
    request=request,
    username='test_user',
    password='test_pass',
    in_app_token='test_token_12345',
    remember_me=False
)
auth_service.session_manager.set_in_app_auth_required(request, True)

# Test in-app authentication handling (service layer)
result = auth_service.handle_in_app_authentication(request)
print(f"In-App Result: {result.result}")
print(f"Message: {result.message}")
print(f"Session ID: {result.session_id}")
```

### 6. Performance Monitoring

**Check service locator performance:**

```python
from stonks_overwatch.core.authentication_locator import get_authentication_cache_status
status = get_authentication_cache_status()
print(f"Access count: {status['access_count']}")
print(f"Factory cached: {status['factory_cached']}")
print(f"Auth service cached: {status['auth_service_cached']}")
print(f"Services registered: {status['factory_services_registered']}")
```

## Security Checklist

✅ **Credential Protection:**
- [ ] Passwords are never logged in plain text (enforced by masked logging)
- [ ] Session credentials are cleared on logout
- [ ] Database credentials are encrypted (BrokersConfiguration model)
- [ ] TOTP codes are not persisted
- [ ] Session IDs are partially masked in logs

✅ **Error Handling:**
- [ ] Error messages don't expose sensitive data (structured error classes)
- [ ] Authentication failures are logged with context
- [ ] Exception handling follows proper hierarchy

✅ **Architecture Security:**
- [ ] Service interfaces prevent unauthorized access
- [ ] Dependency injection maintains secure boundaries
- [ ] Cache status doesn't expose sensitive information

## Integration Points

### Middleware Integration

- **File**: `src/stonks_overwatch/middleware/degiro_auth.py`
- **Purpose**: Protects routes, handles TOTP redirects
- **Key Method**: `_check_authentication()`

### Login View Integration

- **File**: `src/stonks_overwatch/views/login.py`
- **Purpose**: Handles user login UI, delegates authentication to service layer
- **Key Methods**:
  - `_perform_authentication()`: Delegates to AuthenticationService
  - `_handle_in_app_authentication()`: Delegates to AuthenticationService.handle_in_app_authentication()

### Authentication Service Integration

- **File**: `src/stonks_overwatch/services/utilities/authentication_service.py`
- **Purpose**: Core authentication logic including in-app authentication processing
- **Key Methods**:
  - `authenticate_user()`: Main authentication orchestration
  - `handle_totp_authentication()`: TOTP processing
  - `handle_in_app_authentication()`: In-app authentication orchestration
  - `_wait_for_in_app_confirmation()`: In-app polling loop (uses DeGiroService)

### DeGiro Service Integration

- **File**: `src/stonks_overwatch/services/brokers/degiro/client/degiro_client.py`
- **Purpose**: API connectivity, credential validation
- **Key Method**: `check_connection()`

## Emergency Procedures

### Reset Authentication State

```python
# Clear all session data
auth_service.session_manager.clear_session(request)

# Force logout
auth_service.logout_user(request)

# Clear stored credentials
auth_service.credential_service.clear_stored_credentials()
```

### Bypass Authentication (Development Only)

```python
# Manually set authenticated state
auth_service.session_manager.set_authenticated(request, True)
auth_service.session_manager.set_session_id(request, "dev_session")
```

### Database Credential Recovery

```sql
-- Check stored credentials
SELECT broker_name, is_enabled, credentials
FROM stonks_overwatch_brokersconfiguration
WHERE broker_name = 'degiro';

-- Clear stored credentials if corrupted
UPDATE stonks_overwatch_brokersconfiguration
SET credentials = '{}'
WHERE broker_name = 'degiro';
```

## Modern Architecture Patterns

### Service Locator Pattern

```python
# Optimized access with caching
from stonks_overwatch.core.authentication_locator import get_authentication_service
auth_service = get_authentication_service()  # Uses cached instance
```

### Dependency Injection Pattern

```python
# Services receive configurations automatically
from stonks_overwatch.core.factories.authentication_factory import AuthenticationFactory
factory = AuthenticationFactory()
auth_service = factory.get_authentication_service()  # Auto-injection
```

### Interface-Based Architecture

```python
# Type-safe service contracts
from stonks_overwatch.core.interfaces.authentication_service import AuthenticationServiceInterface
def process_auth(auth_service: AuthenticationServiceInterface):
    # Guaranteed to have all required methods
    return auth_service.authenticate_user(request, username, password)
```

## Code Patterns

### Adding New Authentication Check

```python
def new_auth_check(self, request):
    """Template for new authentication checks."""
    try:
        # 1. Check if authentication is needed
        if not self.should_perform_check():
            return self._create_success_response("Check skipped")

        # 2. Perform the check
        result = self.perform_check(request)

        # 3. Handle errors appropriately
        if result.has_error:
            return self._create_error_response(result.error_type, result.message)

        # 4. Return success
        return self._create_success_response("Check completed")

    except Exception as e:
        self.logger.error(f"Error in new auth check: {str(e)}")
        return self._create_error_response(AuthenticationResult.CONNECTION_ERROR, str(e))
```

### Session State Management

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
