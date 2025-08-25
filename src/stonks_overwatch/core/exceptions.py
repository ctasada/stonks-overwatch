"""
Custom exceptions for the core framework.

This module defines custom exceptions used throughout the Stonks Overwatch
application for better error handling and debugging.
"""


class StonksOverwatchException(Exception):  # noqa: N818
    """Base exception for all Stonks Overwatch errors."""

    pass


class BrokerServiceException(StonksOverwatchException):
    """Exception raised for broker service related errors."""

    pass


class PortfolioServiceException(BrokerServiceException):
    """Exception raised for portfolio service errors."""

    pass


class TransactionServiceException(BrokerServiceException):
    """Exception raised for transaction service errors."""

    pass


class DepositServiceException(BrokerServiceException):
    """Exception raised for deposit service errors."""

    pass


class DividendServiceException(BrokerServiceException):
    """Exception raised for dividend service errors."""

    pass


class ServiceRegistryException(StonksOverwatchException):
    """Exception raised for service registry errors."""

    pass


class ServiceFactoryException(StonksOverwatchException):
    """Exception raised for service factory errors."""

    pass


class DataAggregationException(StonksOverwatchException):
    """Exception raised for data aggregation errors."""

    pass


class CredentialsException(StonksOverwatchException):
    """Exception raised for credential related errors."""

    pass
