# Backwards compatibility imports
# These allow existing code to continue importing from services.* while we migrate

# Note: Aggregator imports are commented out to avoid circular imports
# They can be imported directly from their new locations:
# from stonks_overwatch.services.aggregators.portfolio_aggregator import PortfolioAggregatorService
# from .aggregators.portfolio_aggregator import PortfolioAggregatorService
# from .aggregators.deposits_aggregator import DepositsAggregatorService
# from .aggregators.transactions_aggregator import TransactionsAggregatorService
# from .aggregators.dividends_aggregator import DividendsAggregatorService
# from .aggregators.fees_aggregator import FeesAggregatorService
# from .aggregators.account_overview_aggregator import AccountOverviewAggregatorService

# Utilities (commented out to avoid circular imports)
# from .utilities.session_manager import *

# Re-export submodules for compatibility
from . import aggregators, brokers, utilities

# Broker service imports are commented out to avoid circular imports
# They can be imported directly from their new locations:
# from .brokers.degiro.client.degiro_client import DeGiroService, CredentialsManager, DeGiroOfflineModeError
# from .brokers.degiro.services.portfolio_service import PortfolioService as DeGiroPortfolioService
# etc.
