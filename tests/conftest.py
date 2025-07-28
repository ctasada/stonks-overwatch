import os
import tempfile
from functools import wraps

import requests_cache

import pytest


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


class MockBrokerService:
    """Generic mock service class that passes registry validation."""

    def __init__(self, config=None):
        from unittest.mock import MagicMock

        self.config = config
        self._mock = MagicMock()

    def __getattr__(self, name):
        return getattr(self._mock, name)


def _create_mock_services():
    """Create mock service classes that pass registry validation."""
    return {
        "degiro": {
            "portfolio": MockBrokerService,
            "transaction": MockBrokerService,
            "deposit": MockBrokerService,
            "dividend": MockBrokerService,
            "fee": MockBrokerService,
            "account": MockBrokerService,
        },
        "bitvavo": {
            "portfolio": MockBrokerService,
            "transaction": MockBrokerService,
            "deposit": MockBrokerService,
            "dividend": MockBrokerService,
            "fee": MockBrokerService,
            "account": MockBrokerService,
        },
        "ibkr": {
            "portfolio": MockBrokerService,
            "transaction": MockBrokerService,
            "dividend": MockBrokerService,
            "account": MockBrokerService,
        },
    }


def _register_mock_services(registry, mock_services_dict):
    """Register mock services with the registry."""
    for broker_name, services in mock_services_dict.items():
        registry.register_broker_services(broker_name, **services)


@pytest.fixture(autouse=True)
def reset_global_config():
    """Reset the global configuration before each test to ensure clean state."""
    from stonks_overwatch.config.global_config import global_config
    from stonks_overwatch.core.factories.unified_broker_registry import UnifiedBrokerRegistry

    # Reset the global config to force reload
    global_config.reset_for_tests()

    # Initialize unified registry for tests
    try:
        registry = UnifiedBrokerRegistry()
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

    yield
