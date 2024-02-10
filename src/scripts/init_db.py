from scripts.account_import import run as account_import
from scripts.transactions_import import run as transactions_import
from scripts.products_info_import import run as products_info_import

def run():
    account_import()
    transactions_import()
    products_info_import()

if __name__ == '__main__':
    run()