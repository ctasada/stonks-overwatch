"""
Service interfaces and contracts for broker implementations.

This module defines the common interfaces that all broker services
must implement to ensure consistency and interoperability.
"""

from .broker_service import BrokerServiceInterface
from .deposit_service import DepositServiceInterface
from .dividend_service import DividendServiceInterface
from .portfolio_service import PortfolioServiceInterface
from .transaction_service import TransactionServiceInterface

__all__ = [
    'BrokerServiceInterface',
    'PortfolioServiceInterface',
    'TransactionServiceInterface',
    'DepositServiceInterface',
    'DividendServiceInterface',
]
