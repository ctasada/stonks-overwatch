"""
Standardized error message constants for authentication system.

This module defines a comprehensive catalog of error messages used across the
authentication system to ensure consistency, maintainability, and better user experience.
It includes both user-facing messages and technical logging messages.
"""


class UserErrorMessages:
    """User-facing error messages for the authentication system."""

    # Login form validation errors
    CREDENTIALS_REQUIRED = "Username and password are required."
    INVALID_CREDENTIALS = "Invalid username or password. Please try again."
    CONNECTION_ERROR = "Unable to connect to the authentication service. Please check your connection and try again."
    MAINTENANCE_MODE = "The system is temporarily unavailable for maintenance. Please try again later."
    UNEXPECTED_ERROR = "An unexpected error occurred. Please contact support if the problem persists."

    # Two-factor authentication
    TOTP_REQUIRED = "Two-factor authentication code required. Please enter your authenticator code."
    TOTP_INVALID = "Invalid two-factor authentication code. Please try again."
    TOTP_AUTHENTICATION_REQUIRED = "Two-factor authentication is required to continue."

    # Session and access errors
    SESSION_EXPIRED = "Your session has expired. Please log in again."
    ACCESS_DENIED = "Access denied. Please log in to continue."
    MAINTENANCE_MODE_ACCESS_DENIED = "Access to this feature is not available during maintenance mode."

    # Network and service errors
    NETWORK_ERROR = "Network connection error. Please check your internet connection and try again."
    SERVICE_UNAVAILABLE = "The authentication service is temporarily unavailable. Please try again later."
    CONFIGURATION_ERROR = "Authentication configuration error. Please contact support."


class TechnicalErrorMessages:
    """Technical error messages for logging and debugging."""

    # Authentication service errors
    AUTH_SERVICE_INIT_FAILED = "Failed to initialize authentication service"
    AUTH_SERVICE_UNEXPECTED_ERROR = "Unexpected error in authentication service"
    AUTH_CONNECTION_CHECK_FAILED = "Authentication connection check failed"
    AUTH_DEGIRO_CONNECTION_FAILED = "DeGiro connection authentication failed"
    AUTH_TOTP_VALIDATION_FAILED = "TOTP authentication validation failed"

    # Session management errors
    SESSION_DATA_RETRIEVAL_FAILED = "Failed to retrieve session data"
    SESSION_DATA_STORAGE_FAILED = "Failed to store session data"
    SESSION_CLEANUP_FAILED = "Failed to clean up session data"

    # Credential service errors
    CREDENTIAL_VALIDATION_FAILED = "Credential validation failed"
    CREDENTIAL_STORAGE_FAILED = "Failed to store credentials"
    CREDENTIAL_RETRIEVAL_FAILED = "Failed to retrieve credentials"
    CREDENTIAL_CLEARING_FAILED = "Failed to clear stored credentials"

    # Configuration and setup errors
    CONFIG_RETRIEVAL_FAILED = "Failed to retrieve configuration"
    SERVICE_REGISTRATION_FAILED = "Failed to register authentication services"
    DEPENDENCY_INJECTION_FAILED = "Dependency injection failed"

    # Network and external service errors
    DEGIRO_API_CONNECTION_FAILED = "Failed to connect to DeGiro API"
    DEGIRO_API_AUTHENTICATION_FAILED = "DeGiro API authentication failed"
    NETWORK_CONNECTION_ERROR = "Network connection error occurred"
    EXTERNAL_SERVICE_ERROR = "External service error occurred"


class LogMessages:
    """Standardized log messages for authentication operations."""

    # Authentication flow logs
    AUTH_STARTED = "User authentication started"
    AUTH_SUCCESSFUL = "User authentication successful"
    AUTH_FAILED = "User authentication failed"
    LOGIN_SUCCESSFUL = "Login successful"
    LOGOUT_SUCCESSFUL = "User logged out successfully"

    # Two-factor authentication logs
    TOTP_REQUIRED_USER = "TOTP required - prompting user for 2FA code"
    TOTP_AUTHENTICATION_STARTED = "TOTP authentication started"
    TOTP_AUTHENTICATION_SUCCESSFUL = "TOTP authentication successful"
    TOTP_AUTHENTICATION_FAILED = "TOTP authentication failed"
    TOTP_REQUIRED_PRESERVING = "TOTP required - preserving session for 2FA flow"

    # Session management logs
    SESSION_CREATED = "User session created"
    SESSION_UPDATED = "User session updated"
    SESSION_CLEARED = "User session cleared"
    SESSION_EXPIRED = "User session expired"

    # User status logs
    USER_ALREADY_AUTHENTICATED = "User is already authenticated - redirecting to dashboard"
    USER_NOT_AUTHENTICATED = "User not authenticated in session"

    # Middleware and redirection logs
    REDIRECT_PRESERVING_SESSION = "Redirecting to login page (preserving session)"
    REDIRECT_CLEARING_SESSION = "Redirecting to login page (clearing session)"
    MIDDLEWARE_AUTH_CHECK_PASSED = "Middleware authentication check passed"
    MIDDLEWARE_AUTH_CHECK_FAILED = "Middleware authentication check failed"

    # Service operation logs
    SERVICE_INITIALIZED = "Authentication service initialized"
    SERVICE_REGISTERED = "Authentication services registered successfully"
    DEGIRO_STATUS_CHECK_STARTED = "DeGiro status check started"
    DEGIRO_STATUS_CHECK_SUCCESSFUL = "DeGiro status check successful"
    DEGIRO_STATUS_CHECK_FAILED = "DeGiro status check failed"

    # Configuration and setup logs
    CONFIG_LOADED = "Authentication configuration loaded"
    DEPENDENCIES_INJECTED = "Service dependencies injected successfully"
    FACTORY_INITIALIZED = "Authentication factory initialized"


class ErrorCodes:
    """Error codes for systematic error handling and monitoring."""

    # Authentication errors (1000-1099)
    AUTH_INVALID_CREDENTIALS = "AUTH_1001"
    AUTH_CONNECTION_ERROR = "AUTH_1002"
    AUTH_MAINTENANCE_MODE = "AUTH_1003"
    AUTH_CONFIGURATION_ERROR = "AUTH_1004"
    AUTH_UNKNOWN_ERROR = "AUTH_1005"

    # Two-factor authentication errors (1100-1199)
    TOTP_REQUIRED = "AUTH_1101"
    TOTP_INVALID = "AUTH_1102"
    TOTP_TIMEOUT = "AUTH_1103"

    # Session errors (1200-1299)
    SESSION_EXPIRED = "AUTH_1201"
    SESSION_INVALID = "AUTH_1202"
    SESSION_NOT_FOUND = "AUTH_1203"

    # Service errors (1300-1399)
    SERVICE_UNAVAILABLE = "AUTH_1301"
    SERVICE_TIMEOUT = "AUTH_1302"
    SERVICE_CONFIGURATION_ERROR = "AUTH_1303"

    # Network errors (1400-1499)
    NETWORK_CONNECTION_ERROR = "AUTH_1401"
    NETWORK_TIMEOUT = "AUTH_1402"


# Legacy aliases for backward compatibility
class AuthenticationErrorMessages:
    """Legacy error messages - maintained for backward compatibility."""

    # Direct mappings to new user messages
    CREDENTIALS_REQUIRED = UserErrorMessages.CREDENTIALS_REQUIRED
    INVALID_CREDENTIALS = UserErrorMessages.INVALID_CREDENTIALS
    CONNECTION_ERROR = UserErrorMessages.CONNECTION_ERROR
    MAINTENANCE_MODE = UserErrorMessages.MAINTENANCE_MODE
    UNEXPECTED_ERROR = UserErrorMessages.UNEXPECTED_ERROR

    # Middleware specific messages
    SESSION_NOT_AUTHENTICATED = UserErrorMessages.ACCESS_DENIED
    MAINTENANCE_MODE_ACCESS_DENIED = UserErrorMessages.MAINTENANCE_MODE_ACCESS_DENIED
    TOTP_AUTHENTICATION_REQUIRED = UserErrorMessages.TOTP_AUTHENTICATION_REQUIRED
    AUTHENTICATION_FAILED_PREFIX = "Authentication failed"
    AUTHENTICATION_ISSUE_PREFIX = "Authentication issue"
