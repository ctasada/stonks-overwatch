"""
Service interfaces and contracts for broker implementations.

This module defines the common interfaces that all broker services
must implement to ensure consistency and interoperability.
"""

from .account_service import AccountServiceInterface
from .authentication_service import AuthenticationResponse, AuthenticationResult, AuthenticationServiceInterface
from .broker_service import BrokerServiceInterface
from .credential_service import CredentialServiceInterface
from .deposit_service import DepositServiceInterface
from .dividend_service import DividendServiceInterface
from .fee_service import FeeServiceInterface
from .portfolio_service import PortfolioServiceInterface
from .session_manager import SessionManagerInterface
from .transaction_service import TransactionServiceInterface

__all__ = [
    "AccountServiceInterface",
    "AuthenticationServiceInterface",
    "AuthenticationResult",
    "AuthenticationResponse",
    "BrokerServiceInterface",
    "CredentialServiceInterface",
    "DepositServiceInterface",
    "DividendServiceInterface",
    "FeeServiceInterface",
    "PortfolioServiceInterface",
    "SessionManagerInterface",
    "TransactionServiceInterface",
]
