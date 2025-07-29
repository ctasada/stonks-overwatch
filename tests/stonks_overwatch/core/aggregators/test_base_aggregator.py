"""
Tests for BaseAggregator.

This module contains comprehensive tests for the base aggregator class,
covering initialization, broker service management, data collection, and helper methods.
"""

from stonks_overwatch.core.aggregators.base_aggregator import BaseAggregator
from stonks_overwatch.core.service_types import ServiceType
from stonks_overwatch.services.models import PortfolioId

import pytest
from unittest.mock import MagicMock, patch


class ConcreteAggregator(BaseAggregator):
    """Concrete implementation of BaseAggregator for testing."""

    def aggregate_data(self, selected_portfolio: PortfolioId, **kwargs):
        """Simple implementation for testing."""
        return self._collect_and_merge_lists(selected_portfolio, "get_data")


class TestBaseAggregator:
    """Test cases for BaseAggregator."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Clear any singleton instances (legacy BrokerRegistry removed - using unified system)

    @patch("stonks_overwatch.core.aggregators.base_aggregator.BrokerFactory")
    @patch("stonks_overwatch.core.aggregators.base_aggregator.Config")
    def test_initialization(self, mock_config, mock_factory_class):
        """Test aggregator initialization."""
        # Setup
        mock_factory = MagicMock()
        mock_factory_class.return_value = mock_factory

        # Test
        aggregator = ConcreteAggregator(ServiceType.PORTFOLIO)

        # Verify
        assert aggregator._service_type == ServiceType.PORTFOLIO
        assert aggregator._factory is not None

    @patch("stonks_overwatch.core.aggregators.base_aggregator.Config")
    @patch("stonks_overwatch.core.aggregators.base_aggregator.BrokerFactory")
    def test_collect_broker_data_success(self, mock_config, mock_factory_class):
        """Test successful data collection from multiple brokers."""
        # Setup
        mock_factory = MagicMock()
        mock_factory_class.return_value = mock_factory
        mock_config.get_global.return_value = MagicMock()

        # Create aggregator
        aggregator = ConcreteAggregator(ServiceType.PORTFOLIO)

        # Mock broker services
        mock_service1 = MagicMock()
        mock_service1.get_data.return_value = ["data1", "data2"]
        mock_service2 = MagicMock()
        mock_service2.get_data.return_value = ["data3", "data4"]

        aggregator._broker_services = {"broker1": mock_service1, "broker2": mock_service2}

        # Mock _get_enabled_brokers to return both brokers
        with patch.object(aggregator, "_get_enabled_brokers") as mock_get_enabled:
            mock_get_enabled.return_value = ["broker1", "broker2"]

            # Collect data
            portfolio_id = PortfolioId.ALL
            result = aggregator._collect_broker_data(portfolio_id, "get_data")

            # Verify results
            assert len(result) == 2
            assert result["broker1"] == ["data1", "data2"]
            assert result["broker2"] == ["data3", "data4"]

    @patch("stonks_overwatch.core.aggregators.base_aggregator.Config")
    @patch("stonks_overwatch.core.aggregators.base_aggregator.BrokerFactory")
    def test_collect_and_merge_lists(self, mock_config, mock_factory_class):
        """Test collecting and merging data from multiple brokers."""
        # Setup
        mock_factory = MagicMock()
        mock_factory_class.return_value = mock_factory
        mock_config.get_global.return_value = MagicMock()

        # Create aggregator
        aggregator = ConcreteAggregator(ServiceType.PORTFOLIO)

        # Mock _collect_broker_data
        with patch.object(aggregator, "_collect_broker_data") as mock_collect:
            mock_collect.return_value = {"broker1": ["item1", "item2"], "broker2": ["item3", "item4"]}

            # Test without merger function
            portfolio_id = PortfolioId.ALL
            result = aggregator._collect_and_merge_lists(portfolio_id, "get_data")

            # Verify results
            assert len(result) == 4
            assert "item1" in result
            assert "item2" in result
            assert "item3" in result
            assert "item4" in result

    def test_abstract_method_requirement(self):
        """Test that BaseAggregator cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseAggregator(ServiceType.PORTFOLIO)
