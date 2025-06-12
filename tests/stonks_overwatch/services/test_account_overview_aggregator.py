from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.services.aggregators.account_overview_aggregator import AccountOverviewAggregatorService
from stonks_overwatch.services.brokers.bitvavo.services.account_service import (
    AccountOverviewService as BitvavoAccountOverviewService,
)
from stonks_overwatch.services.brokers.degiro.services.account_service import (
    AccountOverviewService as DeGiroAccountOverviewService,
)
from stonks_overwatch.services.models import AccountOverview, PortfolioId

import pytest
from unittest.mock import patch

@pytest.fixture(scope="function", autouse=True)
def setup_broker_registry():
    """Setup broker service registry for tests."""
    from stonks_overwatch.core.factories.broker_registry import BrokerRegistry
    from stonks_overwatch.core.registry_setup import register_broker_services

    # Clear the registry to ensure clean state
    registry = BrokerRegistry()
    registry._brokers.clear()
    registry._broker_capabilities.clear()

    # Register broker services
    register_broker_services()
    yield

    # Clean up after test
    registry._brokers.clear()
    registry._broker_capabilities.clear()

@pytest.fixture(scope="function", autouse=True)
def mock_degiro_get_account_overview():
    with patch.object(DeGiroAccountOverviewService, "get_account_overview") as mock_method:
        mock_method.return_value = [
            AccountOverview(
                datetime="2024-09-16 18:46:52",
                value_datetime="2024-09-16 18:46:52",
                stock_name="",
                stock_symbol="",
                description="Degiro Cash Sweep Transfer",
                type="FLATEX_CASH_SWEEP",
                currency="EUR",
                change=-14.36,

            ),
            AccountOverview(
                datetime="2024-08-29 14:33:41",
                value_datetime="2024-08-29 14:33:41",
                stock_name="Apple Inc",
                stock_symbol="AAPL",
                description="Koop 2 @ 100,000 EUR",
                type="TRANSACTION",
                currency="EUR",
                change=-200.0,
            )
        ]
        yield mock_method

@pytest.fixture(scope="function", autouse=True)
def mock_bitvavo_get_account_overview():
    with patch.object(BitvavoAccountOverviewService, "get_account_overview") as mock_method:
        mock_method.return_value = [
            AccountOverview(
                datetime="2024-08-20 10:30:41",
                value_datetime="2024-08-20 10:30:41",
                stock_name="Bitcoin",
                stock_symbol="BTC",
                description="Bought 1 Bitcoin",
                type="TRANSACTION",
                currency="EUR",
                change=-200.0,
            ),
            AccountOverview(
                datetime="2024-10-20 10:30:41",
                value_datetime="2024-10-20 10:30:41",
                stock_name="Bitcoin",
                stock_symbol="BTC",
                description="Bought 0.5 Bitcoin",
                type="TRANSACTION",
                currency="EUR",
                change=-200.0,
            )
        ]
        yield mock_method

def test_get_account_overview_aggregator(
        setup_broker_registry,
        mock_degiro_get_account_overview,
        mock_bitvavo_get_account_overview
):
    BaseConfig.CONFIG_PATH = "tests/resources/stonks_overwatch/config/sample-config.json"

    aggregator = AccountOverviewAggregatorService()
    overview = aggregator.get_account_overview(PortfolioId.ALL)

    assert overview is not None
    assert len(overview) == 4
    assert overview[0].stock_name == "Bitcoin"
    assert overview[1].description == "Degiro Cash Sweep Transfer"
    assert overview[2].stock_name == "Apple Inc"
    assert overview[3].stock_name == "Bitcoin"

def test_get_account_overview_aggregator_only_degiro(setup_broker_registry, mock_degiro_get_account_overview):
    BaseConfig.CONFIG_PATH = "tests/resources/stonks_overwatch/config/sample-config.json"

    aggregator = AccountOverviewAggregatorService()
    overview = aggregator.get_account_overview(PortfolioId.DEGIRO)

    assert overview is not None
    assert len(overview) == 2
    assert overview[0].description == "Degiro Cash Sweep Transfer"
    assert overview[1].stock_name == "Apple Inc"

def test_get_account_overview_aggregator_only_bitvavo(setup_broker_registry, mock_bitvavo_get_account_overview):
    BaseConfig.CONFIG_PATH = "tests/resources/stonks_overwatch/config/sample-config.json"

    aggregator = AccountOverviewAggregatorService()
    overview = aggregator.get_account_overview(PortfolioId.BITVAVO)

    assert overview is not None
    assert len(overview) == 2
    assert overview[0].description == "Bought 0.5 Bitcoin"
    assert overview[0].stock_name == "Bitcoin"
    assert overview[1].description == "Bought 1 Bitcoin"
    assert overview[1].stock_name == "Bitcoin"
