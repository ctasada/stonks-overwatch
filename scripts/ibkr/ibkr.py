"""poetry run python -m scripts.ibkr.ibkr"""

import json

from scripts.common import setup_django_environment

setup_django_environment()

# Initialize broker registry for standalone script usage
from stonks_overwatch.core.registry_setup import ensure_registry_initialized  # noqa: E402

ensure_registry_initialized()

from stonks_overwatch.services.brokers.ibkr.client.ibkr_service import IbkrService  # noqa: E402

ibkr_service = IbkrService(shutdown_oauth=True)
client = ibkr_service.get_client()

portfolio_accounts = client.portfolio_accounts().data
account_id = portfolio_accounts[0]["accountId"]
# print(json.dumps(portfolio_accounts, indent=4))

# CashBalance
# accounts = ibkr_service.get_portfolio_accounts()
# print(json.dumps(accounts, indent=4))
# summary = ibkr_service.get_account_summary()
# print(json.dumps(summary, indent=4))

# Positions
positions = ibkr_service.get_open_positions()
print(json.dumps(positions, indent=4))

# Performance
# performance = client.account_performance(account_id, "YTD").data
# print(json.dumps(performance, indent=4))

# Exchange
# exchange = client.currency_exchange_rate("USD", "EUR").data
# print(json.dumps(exchange, indent=4))
#
# contract = client.search_contract_by_symbol("JNJ").data
# print(json.dumps(contract, indent=4))
# conid = contract[0]["conid"]
# conid = '8719'
# currency = 'USD'
# conid = "159134192"
# currency = "EUR"
# transactions = ibkr_service.transaction_history(conid, currency)
# print(json.dumps(transactions, indent=4))
# Positions & contract info
# position_contract = client.position_and_contract_info(conid).data
# print(json.dumps(position_contract, indent=4))

# Transaction History per contract
# given_date = datetime.strptime("2023-06-01", "%Y-%m-%d").date()
# today_date = datetime.today().date()
# # Calculate the difference in days
# # days_difference = (today_date - given_date).days
# days_difference = 90
# for position in positions:
#     conid = position["conid"]
#     currency = position["currency"]
#     transactions = client.transaction_history(account_id, conid, currency, str(days_difference)).data
#     print(json.dumps(transactions, indent=4))
#     break

# Market data single symbol
# history = client.marketdata_history_by_symbol('AAPL', period='1w', bar='1d', outside_rth=True).data
# history_sync = client.marketdata_history_by_symbols(['AAPL', 'MSFT', 'GOOG', 'TSLA', 'AMZN'],
#                                                     period='1d', bar='1d', outside_rth=True, run_in_parallel=False)
# print(json.dumps(history, indent=4))
