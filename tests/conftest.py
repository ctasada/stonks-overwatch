import os
import tempfile
from functools import wraps

import requests_cache

from stonks_overwatch.core.interfaces.account_service import AccountServiceInterface
from stonks_overwatch.core.interfaces.deposit_service import DepositServiceInterface
from stonks_overwatch.core.interfaces.dividend_service import DividendServiceInterface
from stonks_overwatch.core.interfaces.fee_service import FeeServiceInterface
from stonks_overwatch.core.interfaces.portfolio_service import PortfolioServiceInterface
from stonks_overwatch.core.interfaces.transaction_service import TransactionServiceInterface

import pytest


# Django setup for test environment - must be done before any Django model imports
def setup_django_for_tests():
    """Properly initialize Django settings for unified architecture tests."""
    import django
    from django.conf import settings

    if not settings.configured:
        # Configure Django with minimal settings for testing
        settings.configure(
            DEBUG=True,
            SECRET_KEY="test-secret-key-for-testing-only",
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.sessions",
                "django.contrib.messages",
                "stonks_overwatch.app_config.StonksOverwatchConfig",
            ],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            USE_TZ=True,
            DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        )
        django.setup()


# Initialize Django before any imports that might reference Django models
setup_django_for_tests()


@pytest.fixture(scope="session")
def temp_cache_path():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = os.path.join(temp_dir, "test_cache.sqlite")
        print(f"Temporary cache path: {temp_db_path}")
        yield temp_db_path
    print("Temporary directory cleaned up")


def create_patched_enabled(original_enabled, temp_cache_path):
    @wraps(original_enabled)
    def patched_enabled(*args, **kwargs):
        # Override the cache_name if it's provided
        kwargs["cache_name"] = temp_cache_path
        # Ensure we're using the sqlite backend
        kwargs["backend"] = "sqlite"
        return original_enabled(*args, **kwargs)

    return patched_enabled


@pytest.fixture(autouse=True)
def use_temp_cache(temp_cache_path, monkeypatch):
    original_enabled = requests_cache.enabled
    patched_enabled = create_patched_enabled(original_enabled, temp_cache_path)
    monkeypatch.setattr(requests_cache, "enabled", patched_enabled)
    print("Patched requests_cache.enabled to use temporary cache")

    # Clear the cache before and after each test
    requests_cache.clear()
    yield
    requests_cache.clear()


def _register_config_classes(registry):
    """Register broker configuration classes with the registry."""
    from stonks_overwatch.config.bitvavo import BitvavoConfig
    from stonks_overwatch.config.degiro import DegiroConfig
    from stonks_overwatch.config.ibkr import IbkrConfig

    registry.register_broker_config("degiro", DegiroConfig)
    registry.register_broker_config("bitvavo", BitvavoConfig)
    registry.register_broker_config("ibkr", IbkrConfig)


def _import_real_services():
    """Import real service classes and return them as dictionaries by broker."""
    # Import DeGiro services
    # Import Bitvavo services
    from stonks_overwatch.services.brokers.bitvavo.services.account_service import (
        AccountOverviewService as BitvavoAccountService,
    )
    from stonks_overwatch.services.brokers.bitvavo.services.deposit_service import (
        DepositsService as BitvavoDepositService,
    )
    from stonks_overwatch.services.brokers.bitvavo.services.dividends_service import (
        DividendsService as BitvavoDividendService,
    )
    from stonks_overwatch.services.brokers.bitvavo.services.fee_service import (
        FeeService as BitvavoFeeService,
    )
    from stonks_overwatch.services.brokers.bitvavo.services.portfolio_service import (
        PortfolioService as BitvavoPortfolioService,
    )
    from stonks_overwatch.services.brokers.bitvavo.services.transaction_service import (
        TransactionsService as BitvavoTransactionService,
    )
    from stonks_overwatch.services.brokers.degiro.services.account_service import (
        AccountOverviewService as DeGiroAccountService,
    )
    from stonks_overwatch.services.brokers.degiro.services.deposit_service import (
        DepositsService as DeGiroDepositService,
    )
    from stonks_overwatch.services.brokers.degiro.services.dividend_service import (
        DividendsService as DeGiroDividendService,
    )
    from stonks_overwatch.services.brokers.degiro.services.fee_service import (
        FeesService as DeGiroFeeService,
    )
    from stonks_overwatch.services.brokers.degiro.services.portfolio_service import (
        PortfolioService as DeGiroPortfolioService,
    )
    from stonks_overwatch.services.brokers.degiro.services.transaction_service import (
        TransactionsService as DeGiroTransactionService,
    )

    # Import IBKR services
    from stonks_overwatch.services.brokers.ibkr.services.account_overview import (
        AccountOverviewService as IbkrAccountService,
    )
    from stonks_overwatch.services.brokers.ibkr.services.dividends import (
        DividendsService as IbkrDividendService,
    )
    from stonks_overwatch.services.brokers.ibkr.services.portfolio import (
        PortfolioService as IbkrPortfolioService,
    )
    from stonks_overwatch.services.brokers.ibkr.services.transactions import (
        TransactionsService as IbkrTransactionService,
    )

    return {
        "degiro": {
            "portfolio": DeGiroPortfolioService,
            "transaction": DeGiroTransactionService,
            "deposit": DeGiroDepositService,
            "dividend": DeGiroDividendService,
            "fee": DeGiroFeeService,
            "account": DeGiroAccountService,
        },
        "bitvavo": {
            "portfolio": BitvavoPortfolioService,
            "transaction": BitvavoTransactionService,
            "deposit": BitvavoDepositService,
            "dividend": BitvavoDividendService,
            "fee": BitvavoFeeService,
            "account": BitvavoAccountService,
        },
        "ibkr": {
            "portfolio": IbkrPortfolioService,
            "transaction": IbkrTransactionService,
            "dividend": IbkrDividendService,
            "account": IbkrAccountService,
        },
    }


def _register_real_services(registry, services_dict):
    """Register real services with the registry."""
    for broker_name, services in services_dict.items():
        registry.register_broker_services(broker_name, **services)


class MockPortfolioService(PortfolioServiceInterface):
    """Mock portfolio service that implements the required interface."""

    def __init__(self, config=None):
        super().__init__()
        self.config = config

    def get_portfolio(self):
        return []


class MockTransactionService(TransactionServiceInterface):
    """Mock transaction service that implements the required interface."""

    def __init__(self, config=None):
        super().__init__()
        self.config = config

    def get_transactions(self, start_date=None, end_date=None):
        return []


class MockDepositService(DepositServiceInterface):
    """Mock deposit service that implements the required interface."""

    def __init__(self, config=None):
        super().__init__()
        self.config = config

    def get_deposits(self):
        return []

    def calculate_cash_account_value(self):
        return {}


class MockDividendService(DividendServiceInterface):
    """Mock dividend service that implements the required interface."""

    def __init__(self, config=None):
        super().__init__()
        self.config = config

    def get_dividends(self):
        return []


class MockFeeService(FeeServiceInterface):
    """Mock fee service that implements the required interface."""

    def __init__(self, config=None):
        super().__init__()
        self.config = config

    def get_fees(self):
        return []


class MockAccountService(AccountServiceInterface):
    """Mock account service that implements the required interface."""

    def __init__(self, config=None):
        super().__init__()
        self.config = config

    def get_account_overview(self):
        return {}


def _create_mock_services():
    """Create mock service classes that pass registry validation."""
    return {
        "degiro": {
            "portfolio": MockPortfolioService,
            "transaction": MockTransactionService,
            "deposit": MockDepositService,
            "dividend": MockDividendService,
            "fee": MockFeeService,
            "account": MockAccountService,
        },
        "bitvavo": {
            "portfolio": MockPortfolioService,
            "transaction": MockTransactionService,
            "deposit": MockDepositService,
            "dividend": MockDividendService,
            "fee": MockFeeService,
            "account": MockAccountService,
        },
        "ibkr": {
            "portfolio": MockPortfolioService,
            "transaction": MockTransactionService,
            "dividend": MockDividendService,
            "account": MockAccountService,
        },
    }


def _register_mock_services(registry, mock_services_dict):
    """Register mock services with the registry."""
    for broker_name, services in mock_services_dict.items():
        registry.register_broker_services(broker_name, **services)


def _register_authentication_services():
    """Register authentication services for tests."""
    try:
        from stonks_overwatch.core.authentication_setup import register_authentication_services
        from stonks_overwatch.core.factories.authentication_factory import AuthenticationFactory

        # Clear any existing authentication factory instances
        if hasattr(AuthenticationFactory, "_instances"):
            AuthenticationFactory._instances.clear()

        # Register authentication services
        auth_factory = AuthenticationFactory()

        if not auth_factory.is_fully_registered():
            register_authentication_services()
            print("Successfully registered authentication services for tests")
        else:
            print("Authentication services already registered for tests")

    except Exception as e:
        print(f"Warning: Could not register authentication services for tests: {e}")


@pytest.fixture(autouse=True)
def reset_global_config():
    """Reset the global configuration before each test to ensure clean state."""
    from stonks_overwatch.config.config import Config
    from stonks_overwatch.core.factories.broker_registry import BrokerRegistry

    # Reset the global config to force reload
    Config.reset_global_for_tests()

    # Clear singleton instances to ensure clean test state
    if hasattr(BrokerRegistry, "_instances"):
        BrokerRegistry._instances.clear()

    # Initialize unified registry for tests (Django is already configured at this point)
    try:
        registry = BrokerRegistry()
        registry.clear_all_registrations()  # Clear any existing registrations
        _register_config_classes(registry)

        # Try to register real service classes for proper test mocking
        try:
            services_dict = _import_real_services()
            _register_real_services(registry, services_dict)
            print("Successfully initialized unified registry for tests (config classes + real services)")
        except ImportError as e:
            print(f"Could not import real services ({e}), falling back to mock services")
            mock_services_dict = _create_mock_services()
            _register_mock_services(registry, mock_services_dict)
            print("Successfully initialized unified registry for tests (config classes + mock services)")

    except Exception as e:
        print(f"Warning: Could not initialize unified registry for tests: {e}")

    # Ensure authentication services are registered for tests
    _register_authentication_services()

    yield
