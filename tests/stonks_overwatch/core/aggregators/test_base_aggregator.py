"""
Tests for BaseAggregator.

This module contains comprehensive tests for the base aggregator class,
covering initialization, broker service management, data collection, and helper methods.
"""

from stonks_overwatch.core.aggregators.base_aggregator import BaseAggregator
from stonks_overwatch.core.factories.broker_registry import ServiceType
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

    @patch("stonks_overwatch.core.aggregators.base_aggregator.UnifiedBrokerFactory")
    @patch("stonks_overwatch.core.aggregators.base_aggregator.Config")
    def test_initialization(self, mock_config, mock_unified_factory_class):
        """Test aggregator initialization with unified factory."""
        # Mock the unified factory instance
        mock_factory = MagicMock()
        mock_unified_factory_class.return_value = mock_factory
        mock_factory.get_available_brokers.return_value = []

        # Mock config
        mock_config.get_global.return_value = MagicMock()

        # Create aggregator
        aggregator = ConcreteAggregator(ServiceType.PORTFOLIO)

        # Verify initialization
        assert aggregator.service_type == ServiceType.PORTFOLIO
        assert aggregator._service_type == ServiceType.PORTFOLIO
        assert aggregator._unified_factory is not None
        mock_factory.get_available_brokers.assert_called_once()

    @patch("stonks_overwatch.core.aggregators.base_aggregator.UnifiedBrokerFactory")
    @patch("stonks_overwatch.core.aggregators.base_aggregator.Config")
    def test_collect_broker_data_success(self, mock_config, mock_unified_factory_class):
        """Test successful data collection from brokers."""
        # Mock setup
        mock_factory = MagicMock()
        mock_unified_factory_class.return_value = mock_factory
        mock_factory.get_available_brokers.return_value = []
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

    @patch("stonks_overwatch.core.aggregators.base_aggregator.UnifiedBrokerFactory")
    @patch("stonks_overwatch.core.aggregators.base_aggregator.Config")
    def test_collect_and_merge_lists(self, mock_config, mock_unified_factory_class):
        """Test the _collect_and_merge_lists helper method."""
        # Mock setup
        mock_factory = MagicMock()
        mock_unified_factory_class.return_value = mock_factory
        mock_factory.get_available_brokers.return_value = []
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
