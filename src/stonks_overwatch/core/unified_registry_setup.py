"""
Unified registry setup module.

This module handles the registration of all broker configurations and services
with the unified broker registry. It should be called during application
initialization to ensure all configurations and services are available.
"""

from stonks_overwatch.config.bitvavo import BitvavoConfig
from stonks_overwatch.config.degiro import DegiroConfig
from stonks_overwatch.config.ibkr import IbkrConfig
from stonks_overwatch.core.factories.unified_broker_registry import UnifiedBrokerRegistry
from stonks_overwatch.services.brokers.bitvavo.services.account_service import (
    AccountOverviewService as BitvavoAccountService,
)
from stonks_overwatch.services.brokers.bitvavo.services.deposit_service import DepositsService as BitvavoDepositService
from stonks_overwatch.services.brokers.bitvavo.services.dividends_service import (
    DividendsService as BitvavoDividendsService,
)
from stonks_overwatch.services.brokers.bitvavo.services.fee_service import FeeService as BitvavoFeeService
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
from stonks_overwatch.services.brokers.ibkr.services.account_overview import (
    AccountOverviewService as IbkrAccountOverviewService,
)
from stonks_overwatch.services.brokers.ibkr.services.dividends import (
    DividendsService as IbkrDividendsService,
)
from stonks_overwatch.services.brokers.ibkr.services.portfolio import (
    PortfolioService as IbkrPortfolioService,
)
from stonks_overwatch.services.brokers.ibkr.services.transactions import (
    TransactionsService as IbkrTransactionService,
)
from stonks_overwatch.utils.core.logger import StonksLogger

logger = StonksLogger.get_logger("stonks_overwatch.core", "[UNIFIED_REGISTRY_SETUP]")


def register_all_brokers() -> None:
    """
    Register all broker configurations and services with the unified registry.

    This is the unified registration function that sets up both configurations
    and services in a single call, eliminating the need for separate registrations.
    """
    registry = UnifiedBrokerRegistry()

    logger.info("Starting unified broker registration...")

    try:
        # Register DeGiro
        registry.register_complete_broker(
            "degiro",
            DegiroConfig,
            portfolio=DeGiroPortfolioService,
            transaction=DeGiroTransactionService,
            deposit=DeGiroDepositService,
            dividend=DeGiroDividendService,
            fee=DeGiroFeeService,
            account=DeGiroAccountService,
        )
        logger.info("Registered DeGiro broker successfully")

        # Register Bitvavo
        registry.register_complete_broker(
            "bitvavo",
            BitvavoConfig,
            portfolio=BitvavoPortfolioService,
            transaction=BitvavoTransactionService,
            deposit=BitvavoDepositService,
            dividend=BitvavoDividendsService,
            fee=BitvavoFeeService,
            account=BitvavoAccountService,
        )
        logger.info("Registered Bitvavo broker successfully")

        # Register IBKR (only supported services)
        registry.register_broker_config("ibkr", IbkrConfig)
        registry.register_broker_services(
            "ibkr",
            portfolio=IbkrPortfolioService,
            transaction=IbkrTransactionService,
            dividend=IbkrDividendsService,
            account=IbkrAccountOverviewService,
            # Note: IBKR doesn't support deposit and fee services
        )
        logger.info("Registered IBKR broker successfully")

        # Validate all registrations
        validation_status = registry.validate_all_registrations()
        if validation_status["all_valid"]:
            logger.info("All broker registrations validated successfully")
            logger.info(f"Registered brokers: {registry.get_fully_registered_brokers()}")
        else:
            logger.warning(f"Some broker registrations have issues: {validation_status}")

    except Exception as e:
        logger.error(f"Failed to register brokers: {e}")
        raise


def ensure_unified_registry_initialized() -> None:
    """
    Ensure the unified registry is initialized with all broker registrations.

    This function can be called multiple times safely - it will only register
    brokers if they haven't been registered yet.
    """
    registry = UnifiedBrokerRegistry()

    # Check if brokers are already registered
    registered_brokers = registry.get_fully_registered_brokers()
    expected_brokers = {"degiro", "bitvavo"}
    # Note: IBKR is not fully registered due to missing required services

    # Check individual registrations to avoid duplicate attempts
    if "degiro" not in registered_brokers and not registry.is_config_registered("degiro"):
        try:
            registry.register_complete_broker(
                "degiro",
                DegiroConfig,
                portfolio=DeGiroPortfolioService,
                transaction=DeGiroTransactionService,
                deposit=DeGiroDepositService,
                dividend=DeGiroDividendService,
                fee=DeGiroFeeService,
                account=DeGiroAccountService,
            )
            logger.info("Registered DeGiro broker successfully")
        except Exception as e:
            logger.warning(f"Failed to register DeGiro: {e}")

    if "bitvavo" not in registered_brokers and not registry.is_config_registered("bitvavo"):
        try:
            registry.register_complete_broker(
                "bitvavo",
                BitvavoConfig,
                portfolio=BitvavoPortfolioService,
                transaction=BitvavoTransactionService,
                deposit=BitvavoDepositService,
                dividend=BitvavoDividendsService,
                fee=BitvavoFeeService,
                account=BitvavoAccountService,
            )
            logger.info("Registered Bitvavo broker successfully")
        except Exception as e:
            logger.warning(f"Failed to register Bitvavo: {e}")

    # Handle IBKR separately due to missing services
    if not registry.is_config_registered("ibkr"):
        try:
            registry.register_broker_config("ibkr", IbkrConfig)
            registry.register_broker_services(
                "ibkr",
                portfolio=IbkrPortfolioService,
                transaction=IbkrTransactionService,
                dividend=IbkrDividendsService,
                account=IbkrAccountOverviewService,
            )
            logger.info("Registered IBKR broker successfully")
        except Exception as e:
            logger.warning(f"Failed to register IBKR: {e}")

    # Check final status
    final_registered = registry.get_fully_registered_brokers()
    final_registered_set = set(final_registered)
    if expected_brokers.issubset(final_registered_set):
        logger.debug(f"Unified registry initialized with brokers: {final_registered}")
    else:
        missing_brokers = expected_brokers - final_registered_set
        logger.debug(
            f"Unified registry partially initialized with brokers: {final_registered}, missing: {missing_brokers}"
        )


# Automatically initialize when this module is imported
try:
    ensure_unified_registry_initialized()
except Exception as e:
    logger.warning(f"Could not automatically initialize unified registry: {e}")
    logger.info("Unified registry will be initialized on first use")
