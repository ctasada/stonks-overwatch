"""Imports all needed data from DeGiro.

This script is intended to be run as a Django script.

The script is used to update or re-create the DB with all the needed data from DeGiro.

Usage:
    poetry run src/manage.py runscript init_db
    poetry run src/manage.py runscript init_db --script-args account
    poetry run src/manage.py runscript init_db --script-args transactions
    poetry run src/manage.py runscript init_db --script-args products
    poetry run src/manage.py runscript init_db --script-args companies
    poetry run src/manage.py runscript init_db --script-args yfinance
"""

import logging
import os

from scripts.commons import IMPORT_FOLDER
from stonks_overwatch.services.degiro.update_service import UpdateService

def init() -> None:
    """Execute needed initializations for the scripts.

    * Creates the folder to put the imported files
    ### Returns:
        None
    """
    if not os.path.exists(IMPORT_FOLDER):
        os.makedirs(IMPORT_FOLDER)

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


def account_import(update_service: UpdateService) -> None:
    """Import DeGiro Account information."""
    logging.info("Importing DeGiro Account Information...")
    update_service.update_account()


def transactions_import(update_service: UpdateService) -> None:
    logging.info("Importing DeGiro Transactions...")
    update_service.update_transactions({"transactions.json": f"{IMPORT_FOLDER}/transactions.json"})


def products_info_import(update_service: UpdateService) -> None:
    """Import Product Information from DeGiro."""
    logging.info("Importing DeGiro Products Information...")
    update_service.update_portfolio()


def company_profile_import(update_service: UpdateService) -> None:
    logging.info("Importing DeGiro Company Profiles...")
    update_service.update_company_profile()

def yfinance(update_service: UpdateService) -> None:
    logging.info("Importing YFinance Data...")
    update_service.update_yfinance()

def run(*args):
    init()

    update_service = UpdateService()

    if "account" in args:
        account_import(update_service)
    elif "transactions" in args:
        transactions_import(update_service)
    elif "products" in args:
        products_info_import(update_service)
    elif "companies" in args:
        company_profile_import(update_service)
    elif "yfinance" in args:
        yfinance(update_service)
    else:
        account_import(update_service)
        transactions_import(update_service)
        products_info_import(update_service)
        company_profile_import(update_service)
        yfinance(update_service)


if __name__ == "__main__":
    run()
