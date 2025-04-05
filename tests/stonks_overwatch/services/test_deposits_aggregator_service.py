from datetime import date

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.services.bitvavo.deposits import DepositsService as BitvavoDepositsService
from stonks_overwatch.services.degiro.deposits import DepositsService as DegiroDepositsService
from stonks_overwatch.services.deposits_aggregator import DepositsAggregatorService
from stonks_overwatch.services.models import Deposit, DepositType, PortfolioId
from stonks_overwatch.utils.localization import LocalizationUtility

import pytest
from unittest.mock import patch

@pytest.fixture(scope="function", autouse=True)
def mock_degiro_get_cash_deposits():
    with patch.object(DegiroDepositsService, "get_cash_deposits") as mock_method:
        mock_method.return_value = [
            Deposit(
                datetime=LocalizationUtility.convert_string_to_datetime("2024-09-16 18:46:52"),
                description="Deposit",
                type=DepositType.DEPOSIT,
                currency="EUR",
                change=10000.0,
            ),
            Deposit(
                datetime=LocalizationUtility.convert_string_to_datetime("2024-10-26 18:46:52"),
                description="Withdrawal",
                type=DepositType.WITHDRAWAL,
                currency="EUR",
                change=-200.0,
            ),
        ]
        yield mock_method

@pytest.fixture(scope="function", autouse=True)
def mock_bitvavo_get_cash_deposits():
    with patch.object(BitvavoDepositsService, "get_cash_deposits") as mock_method:
        mock_method.return_value = [
            Deposit(
                datetime=LocalizationUtility.convert_string_to_datetime("2024-09-16 18:46:52"),
                description="Deposit",
                type=DepositType.DEPOSIT,
                currency="EUR",
                change=1000.0,
            ),
            Deposit(
                datetime=LocalizationUtility.convert_string_to_datetime("2024-10-16 18:46:52"),
                description="Withdrawal",
                type=DepositType.WITHDRAWAL,
                currency="EUR",
                change=-100.0,
            ),
        ]
        yield mock_method

def test_get_deposit_aggregator_service(mock_bitvavo_get_cash_deposits, mock_degiro_get_cash_deposits):
    BaseConfig.CONFIG_PATH = "tests/resources/stonks_overwatch/config/sample-config.json"

    aggregator = DepositsAggregatorService()
    deposits = aggregator.get_cash_deposits(PortfolioId.ALL)

    assert deposits is not None
    assert len(deposits) == 4
    assert deposits[0].type == DepositType.WITHDRAWAL
    assert deposits[0].change == -200.0
    assert deposits[1].type == DepositType.WITHDRAWAL
    assert deposits[1].change == -100.0
    assert deposits[2].type == DepositType.DEPOSIT
    assert deposits[2].change == 10000.0
    assert deposits[3].type == DepositType.DEPOSIT
    assert deposits[3].change == 1000.0

def test_get_deposit_aggregator_service_only_degiro(mock_degiro_get_cash_deposits):
    BaseConfig.CONFIG_PATH = "tests/resources/stonks_overwatch/config/sample-config.json"

    aggregator = DepositsAggregatorService()
    deposits = aggregator.get_cash_deposits(PortfolioId.DEGIRO)

    assert deposits is not None
    assert len(deposits) == 2
    assert deposits[0].type == DepositType.WITHDRAWAL
    assert deposits[0].change == -200.0
    assert deposits[1].type == DepositType.DEPOSIT
    assert deposits[1].change == 10000.0

def test_get_deposit_aggregator_service_only_bitvavo(mock_bitvavo_get_cash_deposits):
    BaseConfig.CONFIG_PATH = "tests/resources/stonks_overwatch/config/sample-config.json"

    aggregator = DepositsAggregatorService()
    deposits = aggregator.get_cash_deposits(PortfolioId.BITVAVO)

    assert deposits is not None
    assert len(deposits) == 2
    assert deposits[0].type == DepositType.WITHDRAWAL
    assert deposits[0].change == -100.0
    assert deposits[1].type == DepositType.DEPOSIT
    assert deposits[1].change == 1000.0

def test_get_cash_deposits_history(mock_bitvavo_get_cash_deposits, mock_degiro_get_cash_deposits):
    BaseConfig.CONFIG_PATH = "tests/resources/stonks_overwatch/config/sample-config.json"

    aggregator = DepositsAggregatorService()
    deposits = aggregator.cash_deposits_history(PortfolioId.ALL)
    assert deposits is not None
    assert len(deposits) == 4

    today_str = LocalizationUtility.format_date_from_date(date.today())

    assert deposits == [{'date': '2024-09-16', 'total_deposit': 11000.0},
                        {'date': '2024-10-16', 'total_deposit': 10900.0},
                        {'date': '2024-10-26', 'total_deposit': 10700.0},
                        {'date': today_str, 'total_deposit': 10700.0}]
