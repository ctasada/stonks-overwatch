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
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stonks_overwatch.settings')
django.setup()

# The import is defined here, so all the Django configuration can be executed
from stonks_overwatch.services.degiro.update_service import UpdateService as DegiroUpdateService  # noqa: E402

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
            * DeGiro
        """)
    )
    default_degiro_import_folder = os.path.join(STONKS_OVERWATCH_DATA_DIR, "import", "degiro")
    parser.add_argument(
        "--import_folder",
        type=str,
        default=os.path.join(STONKS_OVERWATCH_DATA_DIR, "import", "degiro"),
        help=f"Folder to import data from/to. Defaults to: '{default_degiro_import_folder}'"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode. When using debug mode, the script will store the DeGiro data in the import folder."
    )

    parser.add_argument(
        "--degiro_account",
        action="store_true",
        help="Import DeGiro account information"
    )
    parser.add_argument(
        "--degiro_transactions",
        action="store_true",
        help="Import DeGiro transactions"
    )
    parser.add_argument(
        "--degiro_products",
        action="store_true",
        help="Import DeGiro product information"
    )
    parser.add_argument(
        "--degiro_companies",
        action="store_true",
        help="Import DeGiro company profiles"
    )
    parser.add_argument(
        "--degiro_yfinance",
        action="store_true",
        help="Import YFinance data for DeGiro products"
    )

    return parser.parse_args()

def degiro_account_import(update_service: DegiroUpdateService) -> None:
    """Import DeGiro Account information."""
    logging.info("Importing DeGiro Account Information...")
    update_service.update_account()

def degiro_transactions_import(update_service: DegiroUpdateService) -> None:
    logging.info("Importing DeGiro Transactions...")
    update_service.update_transactions()

def degiro_products_info_import(update_service: DegiroUpdateService) -> None:
    """Import Product Information from DeGiro."""
    logging.info("Importing DeGiro Products Information...")
    update_service.update_portfolio()

def degiro_company_profile_import(update_service: DegiroUpdateService) -> None:
    logging.info("Importing DeGiro Company Profiles...")
    update_service.update_company_profile()

def degiro_yfinance(update_service: DegiroUpdateService) -> None:
    logging.info("Importing DeGiro YFinance Data...")
    update_service.update_yfinance()

def main():
    init()
    logging.info("Applying database migrations...")
    call_command("migrate")

    args = parse_args()

    degiro_update_service = DegiroUpdateService(
        import_folder=args.import_folder,
        debug_mode=args.debug
    )

    if args.degiro_account:
        degiro_account_import(degiro_update_service)
    elif args.degiro_transactions:
        degiro_transactions_import(degiro_update_service)
    elif args.degiro_products:
        degiro_products_info_import(degiro_update_service)
    elif args.degiro_companies:
        degiro_company_profile_import(degiro_update_service)
    elif args.degiro_yfinance:
        degiro_yfinance(degiro_update_service)
    else:
        logging.info("DeGiro Importer: No import option selected. Importing all data.")
        degiro_update_service.update_all()

if __name__ == "__main__":
    main()
