"""Imports all needed data from DeGiro.

This script is intended to be run as a Django script.

The script is used to update or re-create the DB with all the needed data from DeGiro.

Usage:
    poetry run src/manage.py runscript init_db
"""

from scripts.account_import import run as account_import
from scripts.company_profile_import import run as company_profile_import
from scripts.products_info_import import run as products_info_import
from scripts.transactions_import import run as transactions_import


def run():
    account_import()
    transactions_import()
    products_info_import()
    company_profile_import()


if __name__ == "__main__":
    run()
