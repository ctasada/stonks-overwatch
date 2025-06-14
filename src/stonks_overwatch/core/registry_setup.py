"""
Registry setup module.

This module handles the registration of all broker services with the broker registry.
It should be called during application initialization to ensure all services are available.
"""

from stonks_overwatch.core.factories.broker_registry import BrokerRegistry
from stonks_overwatch.services.brokers.bitvavo.services.account_service import (
    AccountOverviewService as BitvavoAccountService,
)
from stonks_overwatch.services.brokers.bitvavo.services.deposit_service import DepositsService as BitvavoDepositService
from stonks_overwatch.services.brokers.bitvavo.services.fee_service import FeesService as BitvavoFeeService
from stonks_overwatch.services.brokers.bitvavo.services.portfolio_service import (
    PortfolioService as BitvavoPortfolioService,
)
from stonks_overwatch.services.brokers.bitvavo.services.transaction_service import (
    TransactionsService as BitvavoTransactionService,
)
from stonks_overwatch.services.brokers.degiro.services.account_service import (
    AccountOverviewService as DeGiroAccountService,
)
from stonks_overwatch.services.brokers.degiro.services.deposit_service import DepositsService as DeGiroDepositService
from stonks_overwatch.services.brokers.degiro.services.dividend_service import DividendsService as DeGiroDividendService
from stonks_overwatch.services.brokers.degiro.services.fee_service import FeesService as DeGiroFeeService
from stonks_overwatch.services.brokers.degiro.services.portfolio_service import (
    PortfolioService as DeGiroPortfolioService,
)
from stonks_overwatch.services.brokers.degiro.services.transaction_service import (
    TransactionsService as DeGiroTransactionService,
)


def register_broker_services() -> None:
    """
    Register all broker services with the broker registry.

    This function should be called during application initialization
    to ensure all broker services are available through the registry.
    """
    registry = BrokerRegistry()

    # Register DeGiro services
    registry.register_broker(
        broker_name="degiro",
        portfolio_service=DeGiroPortfolioService,
        transaction_service=DeGiroTransactionService,
        deposit_service=DeGiroDepositService,
        dividend_service=DeGiroDividendService,
        fee_service=DeGiroFeeService,
        account_service=DeGiroAccountService,
    )

    # Register Bitvavo services
    registry.register_broker(
        broker_name="bitvavo",
        portfolio_service=BitvavoPortfolioService,
        transaction_service=BitvavoTransactionService,
        deposit_service=BitvavoDepositService,
        dividend_service=None,  # Bitvavo doesn't support dividends
        fee_service=BitvavoFeeService,
        account_service=BitvavoAccountService,
    )
