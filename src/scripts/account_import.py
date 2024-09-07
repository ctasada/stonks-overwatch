"""Imports DeGiro Account information.

This script is intended to be run as a Django script.

Usage:
    poetry run src/manage.py runscript account_import
"""



from degiro.data.account_overview import AccountOverviewData
from scripts.commons import IMPORT_FOLDER, init


def run():
    """Import DeGiro Account information."""
    init()
    account_overview_data = AccountOverviewData()
    account_overview_data.update_account(
        {
            "account.json": f"{IMPORT_FOLDER}/account.json",
            "account_transform.json": f"{IMPORT_FOLDER}/account_transform.json"
        }
    )


if __name__ == "__main__":
    run()
