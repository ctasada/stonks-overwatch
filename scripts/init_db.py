"""Imports all necessary data from DeGiro.

The script is used to update or re-create the DB with all the necessary data from DeGiro.

Usage:
    poetry run python -m scripts.init_db --help
"""

import logging
import os
import textwrap
from argparse import Namespace

from scripts.common import setup_script_environment
from stonks_overwatch.constants import BrokerName

# Set up Django environment and logging
setup_script_environment()

# Import Django and application modules after setup
from django.core.management import call_command  # noqa: E402

from stonks_overwatch.core.factories.broker_factory import BrokerFactory  # noqa: E402

# The import is defined here, so all the Django configuration can be executed
from stonks_overwatch.services.brokers.bitvavo.services.update_service import (  # noqa: E402
    UpdateService as BitvavoUpdateService,
)
from stonks_overwatch.services.brokers.degiro.services.update_service import (  # noqa: E402
    UpdateService as DegiroUpdateService,
)
from stonks_overwatch.services.brokers.ibkr.services.update_service import (  # noqa: E402
    UpdateService as IbkrUpdateService,
)
from stonks_overwatch.services.brokers.models import BrokersConfigurationRepository  # noqa: E402


def parse_args() -> Namespace:
    """Parse command line arguments.
    ### Returns:
        Namespace: Parsed arguments.
    """
    import argparse

    from stonks_overwatch.settings import STONKS_OVERWATCH_DATA_DIR

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""
        Import data from the brokers.

        Supported brokers are:
            * DEGIRO
            * BITVAVO
            * IBKR (Interactive Brokers)
        """),
    )
    default_import_folder = os.path.join(STONKS_OVERWATCH_DATA_DIR, "import")
    parser.add_argument(
        "--import_folder",
        type=str,
        default=os.path.join(STONKS_OVERWATCH_DATA_DIR, "import"),
        help=f"Folder to import data from/to. Defaults to: '{default_import_folder}'",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode. When using debug mode, the script will store the DeGiro data in the import folder.",
    )

    parser.add_argument("--degiro", action="store_true", help="Import DEGIRO")
    parser.add_argument("--degiro_account", action="store_true", help="Import DEGIRO account information")
    parser.add_argument("--degiro_transactions", action="store_true", help="Import DEGIRO transactions")
    parser.add_argument("--degiro_products", action="store_true", help="Import DEGIRO product information")
    parser.add_argument("--degiro_companies", action="store_true", help="Import DEGIRO company profiles")
    parser.add_argument("--degiro_yfinance", action="store_true", help="Import YFinance data for DEGIRO products")
    parser.add_argument("--degiro_dividends", action="store_true", help="Import DEGIRO dividends data")

    parser.add_argument("--ibkr", action="store_true", help="Import IBKR")
    parser.add_argument("--ibkr_portfolio", action="store_true", help="Import IBKR portfolio information")
    parser.add_argument("--ibkr_transactions", action="store_true", help="Import IBKR transactions")

    parser.add_argument("--bitvavo", action="store_true", help="Import Bitvavo")
    parser.add_argument("--bitvavo_portfolio", action="store_true", help="Import Bitvavo portfolio information")
    parser.add_argument("--bitvavo_transactions", action="store_true", help="Import Bitvavo transactions")

    parser.add_argument("--update_credentials", action="store_true", help="Update credentials for supported brokers")

    return parser.parse_args()


def degiro_account_import(update_service: DegiroUpdateService) -> None:
    """Import DeGiro Account information."""
    logging.info("Importing DEGIRO Account Information...")
    update_service.update_account()


def update_credentials():
    """Update credentials for supported services from config.json."""
    import json
    import os

    from stonks_overwatch.config.config import Config

    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.json")
    if not os.path.exists(config_path):
        logging.error(f"Config file not found: {config_path}")
        return

    with open(config_path, "r") as f:
        config_data = json.load(f)

    config = Config()
    for broker_name in config._factory.get_available_brokers():
        broker_config = config.get_broker_config(broker_name)
        if broker_config is not None:
            broker_config_db = BrokersConfigurationRepository.get_broker_by_name(broker_name)
            if broker_config_db is None:
                logging.warning(f"No configuration found for broker: {broker_name}")
                continue
            credentials = config_data.get(broker_name, {}).get("credentials", {})
            # Here you would update the credentials in your system
            logging.info(f"Updating credentials for {broker_name}: {credentials}")
            broker_config_db.credentials = credentials

            BrokersConfigurationRepository.save_broker_configuration(broker_config_db)

    logging.info("Credentials update completed.")


def degiro_transactions_import(update_service: DegiroUpdateService) -> None:
    logging.info("Importing DEGIRO Transactions...")
    update_service.update_transactions()


def degiro_products_info_import(update_service: DegiroUpdateService) -> None:
    """Import Product Information from DeGiro."""
    logging.info("Importing DEGIRO Products Information...")
    update_service.update_portfolio()


def degiro_company_profile_import(update_service: DegiroUpdateService) -> None:
    logging.info("Importing DEGIRO Company Profiles...")
    update_service.update_company_profile()


def degiro_yfinance(update_service: DegiroUpdateService) -> None:
    logging.info("Importing DEGIRO YFinance Data...")
    update_service.update_yfinance()


def degiro_dividends(update_service: DegiroUpdateService) -> None:
    logging.info("Importing DEGIRO Dividends...")
    update_service.update_dividends()


def ibkr_portfolio(update_service: IbkrUpdateService) -> None:
    logging.info("Importing IBKR Portfolio...")
    update_service.update_portfolio()


def ibkr_transactions(update_service: IbkrUpdateService) -> None:
    logging.info("Importing IBKR Transactions...")
    update_service.update_transactions()


def bitvavo_portfolio(update_service: BitvavoUpdateService) -> None:
    logging.info("Importing Bitvavo Portfolio...")
    update_service.update_portfolio()


def bitvavo_transactions(update_service: BitvavoUpdateService) -> None:
    logging.info("Importing Bitvavo Transactions...")
    update_service.update_transactions()


def get_degiro_update_service(args, broker_factory):
    degiro_import_folder = os.path.join(args.import_folder, BrokerName.DEGIRO.lower())
    degiro_config = broker_factory.create_config(BrokerName.DEGIRO)
    return DegiroUpdateService(
        import_folder=degiro_import_folder, debug_mode=args.debug, config=degiro_config, force_connect=True
    )


def get_ibkr_update_service(args, broker_factory):
    ibkr_import_folder = os.path.join(args.import_folder, BrokerName.IBKR.lower())
    ibkr_config = broker_factory.create_config(BrokerName.IBKR)
    return IbkrUpdateService(import_folder=ibkr_import_folder, debug_mode=args.debug, config=ibkr_config)


def get_bitvavo_update_service(args, broker_factory):
    bitvavo_import_folder = os.path.join(args.import_folder, BrokerName.BITVAVO.lower())
    bitvavo_config = broker_factory.create_config(BrokerName.BITVAVO)
    return BitvavoUpdateService(import_folder=bitvavo_import_folder, debug_mode=args.debug, config=bitvavo_config)


def main():
    logging.info("Applying database migrations...")
    call_command("migrate")

    broker_factory = BrokerFactory()
    args = parse_args()

    actions = [
        (args.degiro_account, degiro_account_import, lambda: get_degiro_update_service(args, broker_factory)),
        (args.degiro_transactions, degiro_transactions_import, lambda: get_degiro_update_service(args, broker_factory)),
        (args.degiro_products, degiro_products_info_import, lambda: get_degiro_update_service(args, broker_factory)),
        (args.degiro_companies, degiro_company_profile_import, lambda: get_degiro_update_service(args, broker_factory)),
        (args.degiro_yfinance, degiro_yfinance, lambda: get_degiro_update_service(args, broker_factory)),
        (args.degiro_dividends, degiro_dividends, lambda: get_degiro_update_service(args, broker_factory)),
        (args.ibkr_portfolio, ibkr_portfolio, lambda: get_ibkr_update_service(args, broker_factory)),
        (args.ibkr_transactions, ibkr_transactions, lambda: get_ibkr_update_service(args, broker_factory)),
        (args.bitvavo_portfolio, bitvavo_portfolio, lambda: get_bitvavo_update_service(args, broker_factory)),
        (args.bitvavo_transactions, bitvavo_transactions, lambda: get_bitvavo_update_service(args, broker_factory)),
        (args.degiro, lambda svc: svc.update_all(), lambda: get_degiro_update_service(args, broker_factory)),
        (args.ibkr, lambda svc: svc.update_all(), lambda: get_ibkr_update_service(args, broker_factory)),
        (args.bitvavo, lambda svc: svc.update_all(), lambda: get_bitvavo_update_service(args, broker_factory)),
        (args.update_credentials, update_credentials, None),
    ]

    for condition, func, service_getter in actions:
        if condition:
            if service_getter is None:
                func()
            else:
                service = service_getter()
                func(service)
            break
    else:
        logging.info("No import option selected. Importing all data.")
        get_degiro_update_service(args, broker_factory).update_all()
        get_ibkr_update_service(args, broker_factory).update_all()
        get_bitvavo_update_service(args, broker_factory).update_all()
        update_credentials()


if __name__ == "__main__":
    main()
