# Authentication System Maintenance Guide

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
print(f"TOTP Required: {session_data.get('show_otp')}")
print(f"Session ID: {session_data.get('session_id')}")
```

**Check credential sources:**

```python
sources = auth_service.credential_service.get_credential_sources(request)
print(f"Has session credentials: {sources['has_session']}")
print(f"Has database credentials: {sources['has_database']}")
print(f"Has config credentials: {sources['has_config']}")
```

### 2. Common Issues and Solutions

| Issue | Symptoms | Solution |
|-------|----------|----------|
| **TOTP credentials lost** | "Username and password required" during 2FA | Check if `store_credentials()` is called in `check_degiro_connection()` |
| **Session cleared unexpectedly** | User logged out after TOTP | Verify `preserve_session=True` for TOTP in middleware |
| **Login form not showing 2FA** | Username/password form shown instead of TOTP | Check if `set_totp_required(request, True)` is called |
| **Remember me not working** | Credentials not saved in database | Verify `store_credentials_in_database()` is called after successful auth |

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
- `[AUTH|SERVICE]`: Main authentication operations
- `[AUTH|SESSION_MANAGER]`: Session state changes
- `[AUTH|CREDENTIAL_SERVICE]`: Credential operations
- `[DEGIRO|AUTH_MIDDLEWARE]`: Middleware authentication checks

**Important log messages:**
- `"TOTP required during connection check"`: TOTP flow initiated
- `"Stored credentials in session"`: Credentials cached for TOTP
- `"User logged out successfully"`: Complete logout
- `"Authentication failed"`: General auth failure

### 5. Testing Authentication Locally

**Test authentication flow:**

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

### 6. Performance Monitoring

**Check service locator performance:**

```python
from stonks_overwatch.core.authentication_locator import get_cache_status
status = get_cache_status()
print(f"Cache hits: {status['cache_access_count']}")
print(f"Is cached: {status['is_cached']}")
```

## Security Checklist

- [ ] Passwords are never logged in plain text
- [ ] Session credentials are cleared on logout
- [ ] Database credentials are encrypted
- [ ] TOTP codes are not persisted
- [ ] Error messages don't expose sensitive data

## Integration Points

### Middleware Integration

- **File**: `src/stonks_overwatch/middleware/degiro_auth.py`
- **Purpose**: Protects routes, handles TOTP redirects
- **Key Method**: `_check_authentication()`

### Login View Integration

- **File**: `src/stonks_overwatch/views/login.py`
- **Purpose**: Handles user login, 2FA submission
- **Key Method**: `_perform_authentication()`

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
auth_service.credential_service.clear_stored_credentials("degiro")
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
