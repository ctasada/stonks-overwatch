"""Imports all needed data from DeGiro.

This script is intended to be run as a Django script.

The script is used to update or re-create the DB with all the needed data from DeGiro.

Usage:
    poetry run src/manage.py runscript init_db
    poetry run src/manage.py runscript init_db --script-args account
    poetry run src/manage.py runscript init_db --script-args transactions
    poetry run src/manage.py runscript init_db --script-args products
    poetry run src/manage.py runscript init_db --script-args companies
"""


from degiro.data.account_overview import AccountOverviewData
from degiro.data.portfolio import PortfolioData
from degiro.data.transactions import TransactionsData
from scripts.commons import IMPORT_FOLDER, init
from scripts.company_profile_import import run as company_profile_import


def account_import():
    """Import DeGiro Account information."""
    print("Importing DeGiro Account Information...")
    account_overview_data = AccountOverviewData()
    account_overview_data.update_account(
        {
            "account.json": f"{IMPORT_FOLDER}/account.json",
            "account_transform.json": f"{IMPORT_FOLDER}/account_transform.json"
        }
    )

def transactions_import():
    print("Importing DeGiro Transactions...")
    transactions = TransactionsData()
    transactions.update_transactions(
        {
            "transactions.json": f"{IMPORT_FOLDER}/transactions.json"
        }
    )

def products_info_import():
    """Import Product Information from DeGiro."""
    print("Importing DeGiro Products Information...")
    portfolio_data = PortfolioData()
    portfolio_data.update_portfolio({
        "products_info.json": f"{IMPORT_FOLDER}/products_info.json",
    })

def run(*args):
    init()

    if 'account' in args:
        account_import()
    elif 'transactions' in args:
        transactions_import()
    elif 'products' in args:
        products_info_import()
    elif 'companies' in args:
        company_profile_import()
    else:
        account_import()
        transactions_import()
        products_info_import()
        company_profile_import()


if __name__ == "__main__":
    run()
