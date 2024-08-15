"""Imports DeGiro Portfolio Growth.

This script is intended to be run as a Django script.

Temporal script to easily test the Dashboard Portfolio methods

Usage:
    poetry run src/manage.py runscript transactions_report
"""
from degiro.views.dashboard import Dashboard
from scripts.commons import IMPORT_FOLDER, save_to_json


def run():
    dashboard = Dashboard()
    cash_contributions = dashboard._calculate_cash_contributions()
    save_to_json(cash_contributions, f"{IMPORT_FOLDER}/portfolio_growth/cash_contributions.json")
    cash_account_value = dashboard._calculate_cash_account_value()
    save_to_json(cash_account_value, f"{IMPORT_FOLDER}/portfolio_growth/cash_account.json")
    products_quotation = dashboard._create_products_quotation()
    save_to_json(products_quotation, f"{IMPORT_FOLDER}/portfolio_growth/product_quotations.json")
    portfolio_value = dashboard._calculate_value()
    save_to_json(portfolio_value, f"{IMPORT_FOLDER}/portfolio_growth/portfolio_value.json")


if __name__ == '__main__':
    run()

"""
# Converts the JSON to a CSV
$ jq .data.cashMovements ./import/backup/account.json | in2csv -f json
"""

# Cash Types
"""
CASH_FUND_NAV_CHANGE - Only 2020, seems to be replaced by FLATEX_CASH_SWEEP
CASH_FUND_TRANSACTION  - Only 2020, seems to be replaced by FLATEX_CASH_SWEEP
CASH_TRANSACTION - >> Real transaction << That's the one we need to track!
    * Description:
        - "iDEAL storting" reprepresent an iDEAL payment
        - "iDEAL Deposit" reprepresent an iDEAL payment
        - "Terugstorting" Money returned to the associated Bank

FLATEX_CASH_SWEEP - Represents currency conversions. It can be ignored.
PAYMENT - Represents a PAYMENT, but only shows data in the description. It should be related with a CASH_TRANSACTION
TRANSACTION - Buy/Sell stocks
"""

"""
description: "DEGIRO Transactiekosten en/of kosten van derden" -> defines costs. TRACK IT
flatexCash: Temporal / Intermediate
description: "DEGIRO Aansluitingskosten 2021 (New York Stock Exchange - NSY)" -> defines Stock Exchange Costs
"""

"""
productId: 15694501 & 15694498 -> "Morgan Stanley EUR Liquidity Fund" -> Used for Conversions
"""
