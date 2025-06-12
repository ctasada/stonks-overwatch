# Backwards compatibility imports for repositories
# These allow existing code to continue importing from repositories.* while we migrate

# DeGiro repositories
from ..services.brokers.degiro.repositories.cash_movements_repository import CashMovementsRepository
from ..services.brokers.degiro.repositories.company_profile_repository import CompanyProfileRepository
from ..services.brokers.degiro.repositories.dividends_repository import DividendsRepository
from ..services.brokers.degiro.repositories.product_info_repository import ProductInfoRepository
from ..services.brokers.degiro.repositories.product_quotations_repository import ProductQuotationsRepository
from ..services.brokers.degiro.repositories.transactions_repository import TransactionsRepository

# YFinance repositories
from ..services.brokers.yfinance.repositories.yfinance_repository import YFinanceRepository
