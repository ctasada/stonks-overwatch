"""
Base aggregation framework for combining broker data.

This package contains the base classes and utilities for creating
aggregators that combine data from multiple broker sources.
"""

from .base_aggregator import BaseAggregator
from .data_merger import DataMerger

__all__ = [
    "BaseAggregator",
    "DataMerger",
]
