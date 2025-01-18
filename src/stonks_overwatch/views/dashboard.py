import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views import View

from stonks_overwatch.services.deposits_aggregator import DepositsAggregatorService
from stonks_overwatch.services.models import DailyValue
from stonks_overwatch.services.portfolio_aggregator import PortfolioAggregatorService
from stonks_overwatch.utils.localization import LocalizationUtility


@dataclass
class PortfolioMetrics:
    total_return: float
    annualized_return: float
    cumulative_returns: dict[datetime, float]
    total_days: int
    total_cashflows: float


class Dashboard(View):
    """Dashboard view handling portfolio performance and value visualization.
    This view provides both HTML and JSON endpoints for accessing portfolio data,
    with configurable time intervals and view types. Data is cached to optimize
    performance.
    """

    logger = logging.getLogger("stocks_portfolio.dashboard.views")
    CACHE_KEY_PORTFOLIO = "portfolio_value"
    CACHE_TIMEOUT = 60 * 5  # 5 minutes

    VALID_INTERVALS = frozenset({"YTD", "MTD", "1D", "1W", "1M", "3M", "6M", "1Y", "3Y", "5Y", "ALL"})
    VALID_VIEWS = frozenset({"performance", "value"})

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.deposits = DepositsAggregatorService()
        self.portfolio = PortfolioAggregatorService()

    def get(self, request) -> JsonResponse | HttpResponse:
        """Handle GET request for dashboard view."""
        if request.GET.get("format") == "json":
            return self._handle_json_request(request)

        return render(request, "dashboard.html", {})

    def _handle_json_request(self, request) -> JsonResponse:
        """Process JSON format request and return portfolio data."""
        interval = self._parse_request_interval(request)
        view = self._parse_request_view(request)

        self.logger.debug(f"Rendering dashboard view with interval: {interval} and view type: {view}")

        portfolio_value = self._get_portfolio_value()

        start_date = self._get_interval_start_date(interval)
        if start_date:
            portfolio_value = [item for item in portfolio_value if item['x'] >= start_date]
        else:
            start_date = portfolio_value[0]['x']

        performance_twr = self._calculate_performance_twr(portfolio_value, start_date)
        return JsonResponse({
            "portfolio": {
                "value": {"portfolio_value": portfolio_value},
                "performance": performance_twr,
            }
        })

    @staticmethod
    def _get_interval_start_date(interval: str) -> str|None:  # noqa: C901
        """Get start date for the given interval."""
        today = datetime.today()
        match interval:
            case "YTD":
                return today.replace(month=1, day=1).strftime(LocalizationUtility.DATE_FORMAT)
            case "MTD":
                return today.replace(day=1).strftime(LocalizationUtility.DATE_FORMAT)
            case "1D":
                return (today - pd.DateOffset(days=1)).strftime(LocalizationUtility.DATE_FORMAT)
            case "1W":
                return (today - pd.DateOffset(weeks=1)).strftime(LocalizationUtility.DATE_FORMAT)
            case "1M":
                return (today - pd.DateOffset(months=1)).strftime(LocalizationUtility.DATE_FORMAT)
            case "3M":
                return (today - pd.DateOffset(months=3)).strftime(LocalizationUtility.DATE_FORMAT)
            case "6M":
                return (today - pd.DateOffset(months=6)).strftime(LocalizationUtility.DATE_FORMAT)
            case "1Y":
                return (today - pd.DateOffset(years=1)).strftime(LocalizationUtility.DATE_FORMAT)
            case "3Y":
                return (today - pd.DateOffset(years=3)).strftime(LocalizationUtility.DATE_FORMAT)
            case "5Y":
                return (today - pd.DateOffset(years=5)).strftime(LocalizationUtility.DATE_FORMAT)
            case _:
                return None

    def _parse_request_interval(self, request) -> str:
        """Parse interval from request query parameters."""
        interval = request.GET.get("interval", "YTD")
        if interval not in Dashboard.VALID_INTERVALS:
            self.logger.warning(f"Invalid time range provided: {interval}. Defaulting to 'YTD'.")
            interval = "YTD"

        return interval

    def _parse_request_view(self, request) -> str:
        """Parse view type from request query parameters."""
        view = request.GET.get("type", "value")
        if view not in Dashboard.VALID_VIEWS:
            self.logger.warning(f"Invalid view type provided: {view}. Defaulting to 'value'.")
            view = "value"

        return view

    def _get_portfolio_value(self) -> List[DailyValue]:
        """Get historical portfolio value."""
        portfolio_value = cache.get(Dashboard.CACHE_KEY_PORTFOLIO)

        if portfolio_value is None:
            portfolio_value = self.portfolio.calculate_historical_value()

            cache.set(Dashboard.CACHE_KEY_PORTFOLIO, portfolio_value, timeout=Dashboard.CACHE_TIMEOUT)

        return portfolio_value

    @staticmethod
    def _calculate_twr(dates: List[str], values: List[float], cashflows: List[float]) -> PortfolioMetrics:
        """
        Calculate Time-Weighted Return (TWR) for an investment portfolio.

        Parameters:
        dates (list): List of datetime objects representing dates of values/cashflows
        values (list): List of portfolio values at each date
        cashflows (list): List of cashflows (positive for inflows, negative for outflows)
                         Same length as dates and values, 0 if no cashflow on that date

        Returns:
        float: Time-weighted return as a decimal (e.g., 0.05 for 5% return)
        dict: Additional metrics including sub-period returns
        """
        if len(dates) != len(values) or len(dates) != len(cashflows):
            raise ValueError("All input lists must have the same length")

        if len(dates) < 2:
            raise ValueError("Need at least two periods to calculate returns")

        # Convert dates to datetime if they're strings
        dates = [d if isinstance(d, datetime) else datetime.strptime(d, '%Y-%m-%d')
                 for d in dates]

        # Calculate sub-period returns
        cumulative_returns = {}
        modified_values = values.copy()

        # Calculate daily returns and accumulate
        cumulative_return = 1.0

        for i in range(len(dates)-1):
            start_value = modified_values[i]
            if start_value == 0:
                continue  # Skip periods with zero starting value to avoid division by zero

            end_value = modified_values[i+1]
            cashflow = cashflows[i+1]

            # Adjust end value for any cashflows
            adjusted_end_value = end_value - cashflow

            # Update cumulative return
            daily_return = (adjusted_end_value - start_value) / start_value
            cumulative_return *= (1 + daily_return)
            cumulative_returns[dates[i]] = cumulative_return - 1

            # Modify next period's starting value to include cashflow
            if i < len(dates)-2:
                modified_values[i+1] = end_value

        # Calculate TWR
        total_return = cumulative_return - 1

        # Calculate annualized TWR
        total_days = (dates[-1] - dates[0]).days
        annualized_return = (1 + total_return) ** (365.25 / total_days) - 1

        # Prepare results
        return PortfolioMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            cumulative_returns=cumulative_returns,
            total_days=total_days,
            total_cashflows=sum(cashflows)
        )

    def _calculate_performance_twr(
            self,
            portfolio_value: List[Dict[str, float]],
            start_date: Optional[str]=None
    ) -> List[Dict[str, float]]:
        """
        Calculate portfolio performance using TWR method.

        Args:
            portfolio_value: List of dictionaries containing daily portfolio values
            start_date: Optional start date for calculations (default: earliest date)

        Returns:
            List of dictionaries containing dates and cumulative returns
        """
        deposits = sorted(
            self.deposits.get_cash_deposits(),
            key=lambda k: k.date
        )

        cash_flows = defaultdict(float)
        for item in deposits:
            cash_flows[item.date] += item.change

        market_value_per_day = { item['x']: item['y'] for item in portfolio_value }

        if not start_date:
            start_date = list(market_value_per_day.keys())[0]
        end_date = max(list(cash_flows.keys())[-1], list(market_value_per_day.keys())[-1])

        date_range = pd.date_range(
            start=start_date,
            end=end_date,
            freq="B"  # Business days (excludes weekends)
        )

        dates = []
        daily_cash_flows = []
        market_values = []

        for day in date_range:
            day_str = day.strftime("%Y-%m-%d")
            dates.append(day_str)
            daily_cash_flows.append(cash_flows.get(day_str, 0.0))
            market_values.append(market_value_per_day.get(day_str, 0.0))

        twr = self._calculate_twr(dates, market_values, daily_cash_flows)

        return [
            DailyValue(x=LocalizationUtility.format_date_from_date(k), y=v)
            for k, v in twr.cumulative_returns.items()
        ]
