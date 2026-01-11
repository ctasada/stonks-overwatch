"""
Service type definitions for the unified broker architecture.

This module provides the ServiceType enumeration used throughout the broker
system to identify different types of services that brokers can provide.
"""

from enum import Enum


class ServiceType(Enum):
    """Enumeration of available service types."""

    PORTFOLIO = "portfolio"
    TRANSACTION = "transaction"
    DEPOSIT = "deposit"
    DIVIDEND = "dividend"
    FEE = "fee"
    ACCOUNT = "account"
    AUTHENTICATION = "authentication"
