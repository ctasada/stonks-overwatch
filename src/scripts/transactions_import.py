"""Imports DeGiro Transaction information.

This script is intended to be run as a Django script.

Usage:
    poetry run src/manage.py runscript transactions_import
"""

from degiro.data.transactions import TransactionsData
from scripts.commons import IMPORT_FOLDER, init


def run():
    init()
    transactions = TransactionsData()
    transactions.update_account(
        {
            "transactions.json": f"{IMPORT_FOLDER}/transactions.json"
        }
    )

if __name__ == "__main__":
    run()
