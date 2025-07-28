"""
Unified registry setup module.

This module handles the registration of all broker configurations and services
with the unified broker registry. It should be called during application
initialization to ensure all configurations and services are available.
"""

from typing import Any, Dict, Optional

from stonks_overwatch.config.bitvavo import BitvavoConfig
from stonks_overwatch.config.degiro import DegiroConfig
from stonks_overwatch.config.ibkr import IbkrConfig
from stonks_overwatch.core.factories.unified_broker_registry import UnifiedBrokerRegistry
from stonks_overwatch.core.service_types import ServiceType
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


# Configuration-driven broker definitions
BROKER_CONFIGS: Dict[str, Dict[str, Any]] = {
    "degiro": {
        "config": DegiroConfig,
        "services": {
            ServiceType.PORTFOLIO: DeGiroPortfolioService,
            ServiceType.TRANSACTION: DeGiroTransactionService,
            ServiceType.DEPOSIT: DeGiroDepositService,
            ServiceType.DIVIDEND: DeGiroDividendService,
            ServiceType.FEE: DeGiroFeeService,
            ServiceType.ACCOUNT: DeGiroAccountService,
        },
        "supports_complete_registration": True,
    },
    "bitvavo": {
        "config": BitvavoConfig,
        "services": {
            ServiceType.PORTFOLIO: BitvavoPortfolioService,
            ServiceType.TRANSACTION: BitvavoTransactionService,
            ServiceType.DEPOSIT: BitvavoDepositService,
            ServiceType.DIVIDEND: BitvavoDividendsService,
            ServiceType.FEE: BitvavoFeeService,
            ServiceType.ACCOUNT: BitvavoAccountService,
        },
        "supports_complete_registration": True,
    },
    "ibkr": {
        "config": IbkrConfig,
        "services": {
            ServiceType.PORTFOLIO: IbkrPortfolioService,
            ServiceType.TRANSACTION: IbkrTransactionService,
            ServiceType.DIVIDEND: IbkrDividendsService,
            ServiceType.ACCOUNT: IbkrAccountOverviewService,
            # Note: IBKR doesn't support deposit and fee services
        },
        "supports_complete_registration": False,  # Missing required services
    },
}


def get_broker_config(broker_name: str) -> Optional[Dict[str, Any]]:
    """
    Get the configuration for a specific broker.

    Args:
        broker_name: Name of the broker to get configuration for

    Returns:
        Broker configuration dictionary or None if not found
    """
    return BROKER_CONFIGS.get(broker_name)


def get_all_broker_names() -> list[str]:
    """
    Get all available broker names from the configuration.

    Returns:
        List of all configured broker names
    """
    return list(BROKER_CONFIGS.keys())


def register_all_brokers() -> None:
    """
    Register all broker configurations and services with the unified registry.

    This function uses the BROKER_CONFIGS dictionary to register all brokers
    in a configuration-driven manner, eliminating code duplication.
    """
    registry = UnifiedBrokerRegistry()

    logger.info("Starting configuration-driven broker registration...")

    successfully_registered = []
    failed_registrations = []

    for broker_name, broker_config in BROKER_CONFIGS.items():
        try:
            config_class = broker_config["config"]
            services = broker_config["services"]
            supports_complete = broker_config.get("supports_complete_registration", False)

            if supports_complete:
                # Use complete registration for brokers with all required services
                registry.register_complete_broker(
                    broker_name,
                    config_class,
                    **{service_type.value: service_class for service_type, service_class in services.items()},
                )
                logger.info(f"Registered {broker_name} broker using complete registration")
            else:
                # Use separate registration for brokers missing required services
                registry.register_broker_config(broker_name, config_class)
                registry.register_broker_services(
                    broker_name,
                    **{service_type.value: service_class for service_type, service_class in services.items()},
                )
                logger.info(f"Registered {broker_name} broker using separate registration")

            successfully_registered.append(broker_name)

        except Exception as e:
            logger.error(f"Failed to register {broker_name} broker: {e}")
            failed_registrations.append((broker_name, str(e)))

    # Report results
    if successfully_registered:
        logger.info(f"Successfully registered {len(successfully_registered)} brokers: {successfully_registered}")

    if failed_registrations:
        logger.warning(
            f"Failed to register {len(failed_registrations)} brokers: {[name for name, _ in failed_registrations]}"
        )

    # Validate all registrations
    try:
        validation_status = registry.validate_all_registrations()
        if validation_status["all_valid"]:
            logger.info("All broker registrations validated successfully")
            logger.info(f"Fully registered brokers: {registry.get_fully_registered_brokers()}")
        else:
            logger.warning(f"Some broker registrations have validation issues: {validation_status}")
    except Exception as e:
        logger.error(f"Failed to validate broker registrations: {e}")


def ensure_unified_registry_initialized() -> None:
    """
    Ensure the unified registry is initialized with all broker registrations.

    This function can be called multiple times safely - it will only register
    brokers if they haven't been registered yet. Uses configuration-driven approach.
    """
    registry = UnifiedBrokerRegistry()

    # Check if any brokers are missing registration
    missing_brokers = []
    for broker_name in get_all_broker_names():
        if not registry.is_config_registered(broker_name):
            missing_brokers.append(broker_name)

    if not missing_brokers:
        # All brokers already registered
        registered_brokers = registry.get_fully_registered_brokers()
        logger.debug(f"Unified registry already initialized with brokers: {registered_brokers}")
        return

    logger.info(f"Initializing missing brokers: {missing_brokers}")

    # Register missing brokers using configuration-driven approach
    for broker_name in missing_brokers:
        broker_config = get_broker_config(broker_name)
        if not broker_config:
            logger.warning(f"No configuration found for broker: {broker_name}")
            continue

        try:
            config_class = broker_config["config"]
            services = broker_config["services"]
            supports_complete = broker_config.get("supports_complete_registration", False)

            if supports_complete:
                registry.register_complete_broker(
                    broker_name,
                    config_class,
                    **{service_type.value: service_class for service_type, service_class in services.items()},
                )
                logger.info(f"Registered {broker_name} broker successfully")
            else:
                registry.register_broker_config(broker_name, config_class)
                registry.register_broker_services(
                    broker_name,
                    **{service_type.value: service_class for service_type, service_class in services.items()},
                )
                logger.info(f"Registered {broker_name} broker successfully (separate registration)")

        except Exception as e:
            logger.warning(f"Failed to register {broker_name}: {e}")

    # Check final status
    final_registered = registry.get_fully_registered_brokers()
    expected_complete_brokers = {
        name for name, config in BROKER_CONFIGS.items() if config.get("supports_complete_registration", False)
    }

    final_registered_set = set(final_registered)
    if expected_complete_brokers.issubset(final_registered_set):
        logger.debug(f"Unified registry initialized successfully with brokers: {final_registered}")
    else:
        missing_complete = expected_complete_brokers - final_registered_set
        logger.debug(
            f"Unified registry initialized with brokers: {final_registered}, "
            f"missing complete registration: {missing_complete}"
        )


# Automatically initialize when this module is imported
try:
    ensure_unified_registry_initialized()
except Exception as e:
    logger.warning(f"Could not automatically initialize unified registry: {e}")
    logger.info("Unified registry will be initialized on first use")
