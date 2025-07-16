"""Imports all necessary data from DeGiro.

The script is used to update or re-create the DB with all the necessary data from DeGiro.

Usage:
    poetry run python ./scripts/init_db.py --help
"""

import logging
import os
import sys
import textwrap
from argparse import Namespace

import django
from django.core.management import call_command

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stonks_overwatch.settings")
django.setup()

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


def init() -> None:
    """Execute the necessary initializations for the scripts.
    ### Returns:
        None
    """
    # Configure logging for the stonks_overwatch module
    stonks_overwatch_logger = logging.getLogger("stonks_overwatch")
    stonks_overwatch_logger.setLevel(logging.INFO)

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create a formatter and add it to the console handler
    _format = "%(levelname)s %(asctime)s %(module)s %(message)s"
    formatter = logging.Formatter(_format)
    console_handler.setFormatter(formatter)

    # Configure logging
    logging.basicConfig(level=logging.INFO, format=_format)


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

    return parser.parse_args()


def degiro_account_import(update_service: DegiroUpdateService) -> None:
    """Import DeGiro Account information."""
    logging.info("Importing DEGIRO Account Information...")
    update_service.update_account()


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


def main():
    init()
    logging.info("Applying database migrations...")
    call_command("migrate")

    args = parse_args()

    degiro_import_folder = os.path.join(args.import_folder, "degiro")
    ibkr_import_folder = os.path.join(args.import_folder, "ibkr")
    bitvavo_import_folder = os.path.join(args.import_folder, "bitvavo")

    degiro_update_service = DegiroUpdateService(import_folder=degiro_import_folder, debug_mode=args.debug)
    ibkr_update_service = IbkrUpdateService(import_folder=ibkr_import_folder, debug_mode=args.debug)
    bitvavo_update_service = BitvavoUpdateService(import_folder=bitvavo_import_folder, debug_mode=args.debug)

    actions = [
        (args.degiro_account, degiro_account_import, degiro_update_service),
        (args.degiro_transactions, degiro_transactions_import, degiro_update_service),
        (args.degiro_products, degiro_products_info_import, degiro_update_service),
        (args.degiro_companies, degiro_company_profile_import, degiro_update_service),
        (args.degiro_yfinance, degiro_yfinance, degiro_update_service),
        (args.degiro_dividends, degiro_dividends, degiro_update_service),
        (args.ibkr_portfolio, ibkr_portfolio, ibkr_update_service),
        (args.ibkr_transactions, ibkr_transactions, ibkr_update_service),
        (args.bitvavo_portfolio, bitvavo_portfolio, bitvavo_update_service),
        (args.bitvavo_transactions, bitvavo_transactions, bitvavo_update_service),
        (args.degiro, lambda svc: svc.update_all(), degiro_update_service),
        (args.ibkr, lambda svc: svc.update_all(), ibkr_update_service),
        (args.bitvavo, lambda svc: svc.update_all(), bitvavo_update_service),
    ]

    for condition, func, service in actions:
        if condition:
            func(service)
            break
    else:
        logging.info("No import option selected. Importing all data.")
        degiro_update_service.update_all()
        ibkr_update_service.update_all()
        bitvavo_update_service.update_all()


if __name__ == "__main__":
    main()
