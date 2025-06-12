from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views import View

from stonks_overwatch.services.aggregators.deposits_aggregator import DepositsAggregatorService
from stonks_overwatch.services.aggregators.portfolio_aggregator import PortfolioAggregatorService
from stonks_overwatch.services.models import DailyValue, PortfolioId
from stonks_overwatch.services.utilities.session_manager import SessionManager
from stonks_overwatch.utils.localization import LocalizationUtility
from stonks_overwatch.utils.logger import StonksLogger

@dataclass
class PortfolioMetrics:
    total_return: float
    annualized_return: float
    cumulative_returns: dict[datetime, float]
    total_days: int
    total_cashflows: float

@dataclass
class PortfolioPerformance:
    twr: List[Dict[str, float]]
    annual_twr: Dict[str, float]
    monthly_twr: Dict[str, Dict[str, float]]

class Dashboard(View):
    """Dashboard view handling portfolio performance and value visualization.
    This view provides both HTML and JSON endpoints for accessing portfolio data,
    with configurable time intervals and view types. Data is cached to optimize
    performance.
    """

    logger = StonksLogger.get_logger("stonks_overwatch.dashboard.views", "[VIEW|DASHBOARD]")
    CACHE_KEY_PORTFOLIO = "portfolio_value"
    CACHE_TIMEOUT = 60 * 5  # 5 minutes

    VALID_INTERVALS = frozenset({"YTD", "MTD", "1M", "3M", "6M", "1Y", "3Y", "5Y", "ALL"})
    VALID_VIEWS = frozenset({"performance", "value"})

    # Data quality threshold: warn if daily return exceeds 20%
    LARGE_RETURN_THRESHOLD = 0.20

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.deposits = DepositsAggregatorService()
        self.portfolio = PortfolioAggregatorService()

    def get(self, request) -> JsonResponse | HttpResponse:
        """Handle GET request for a dashboard view."""

        data = self.__calculate_dashboard_data(request)

        if request.headers.get('Accept') == 'application/json':
            return JsonResponse(data)

        return render(request, "dashboard.html", data)

    def __calculate_dashboard_data(self, request) -> dict:
        """Process JSON format request and return portfolio data."""
        interval = self._parse_request_interval(request)
        view = self._parse_request_view(request)
        selected_portfolio = SessionManager.get_selected_portfolio(request)

        self.logger.debug(f"Rendering dashboard view with interval: {interval} and view type: {view}")

        data = self.deposits.cash_deposits_history(selected_portfolio)
        cash_contributions = [{"x": item["date"], "y": item["total_deposit"]} for item in data]

        portfolio_value = self._get_portfolio_value(selected_portfolio)

        start_date = self._get_interval_start_date(interval)
        if start_date:
            portfolio_value = self.__filter_dashboard_values(portfolio_value, start_date)
            cash_contributions = self.__filter_dashboard_values(cash_contributions, start_date)
        else:
            start_date = portfolio_value[0]['x']

        performance_twr = self._calculate_portfolio_performance(selected_portfolio, portfolio_value, start_date)
        return {
            "portfolio": {
                "portfolio_value": portfolio_value,
                "cash_contributions": cash_contributions,
                "performance": performance_twr.twr,
                "annual_twr": performance_twr.annual_twr,
                "monthly_twr": performance_twr.monthly_twr
            }
        }

    @staticmethod
    def __filter_dashboard_values(data_values: List[DailyValue], start_date: str) -> List[DailyValue]:
        # Ensure the list is sorted by date
        data_values.sort(key=lambda item: item['x'])

        # Find the index of the first element where 'x' is greater than or equal to start_date
        index = next((i for i, item in enumerate(data_values) if item['x'] >= start_date), None)

        # If start_date is between values, include the previous element
        if index is not None and index > 0:
            previous_value = data_values[index - 1]['y']
            data_values.insert(index, {'x': start_date, 'y': previous_value})
        elif index is None:
            return []

        # Return the filtered list
        return data_values[index:] if index is not None else []


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
        interval = request.GET.get("interval", "ALL")
        if interval not in Dashboard.VALID_INTERVALS:
            self.logger.warning(f"Invalid time range provided: {interval}. Defaulting to 'ALL'.")
            interval = "ALL"

        return interval

    def _parse_request_view(self, request) -> str:
        """Parse view type from request query parameters."""
        view = request.GET.get("type", "value")
        if view not in Dashboard.VALID_VIEWS:
            self.logger.warning(f"Invalid view type provided: {view}. Defaulting to 'value'.")
            view = "value"

        return view

    def _get_portfolio_value(self, selected_portfolio: PortfolioId) -> List[DailyValue]:
        """Get historical portfolio value."""
        portfolio_value = cache.get(Dashboard.CACHE_KEY_PORTFOLIO)

        if portfolio_value is None:
            portfolio_value = self.portfolio.calculate_historical_value(selected_portfolio)

            cache.set(Dashboard.CACHE_KEY_PORTFOLIO, portfolio_value, timeout=Dashboard.CACHE_TIMEOUT)


        return portfolio_value

    @staticmethod
    def _calculate_twr(
            date_range: list[str], market_value_per_day: dict[str, float], daily_cash_flows: dict[str, float]
    ) -> PortfolioMetrics:
        """
        Calculate Time-Weighted Return (TWR) for an investment portfolio.

        Parameters:
        date_range (list): List of datetime objects representing dates of values/cashflows
        market_value_per_day (dict[day, value]): List of portfolio values at each date
        daily_cash_flows (dict[day, value]): List of cashflows (positive for inflows, negative for outflows)
                         Same length as dates and values, 0 if no cashflow on that date

        Returns:
        float: Time-weighted return as a decimal (e.g., 0.05 for 5% return)
        dict: Additional metrics including sub-period returns
        """

        # Initialize lists for dates, values, and cashflows
        dates = []
        cashflows = []
        values = []

        for day in date_range:
            dates.append(day)
            cashflows.append(daily_cash_flows.get(day, 0.0))
            values.append(market_value_per_day.get(day, 0.0))

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

        logger = StonksLogger.get_logger("stonks_overwatch.dashboard.twr", "[TWR|CALCULATION]")

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

            # Data quality check: warn about unusually large daily returns
            if abs(daily_return) > Dashboard.LARGE_RETURN_THRESHOLD:
                logger.warning(f"Large daily return detected: {daily_return:.2%} from "
                             f"{dates[i].strftime('%Y-%m-%d')} to {dates[i+1].strftime('%Y-%m-%d')} "
                             f"(€{start_value:,.2f} → €{end_value:,.2f}, cashflow: €{cashflow:,.2f}). "
                             f"This may indicate data quality issues or corporate actions.")

            # Fix: Attribute the return to the END date of the period, not the start date
            cumulative_returns[dates[i+1]] = cumulative_return - 1

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

    @staticmethod
    def __default_monthly_values():
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        return dict.fromkeys(months, 0.0)

    def _calculate_portfolio_performance(
            self,
            selected_portfolio: PortfolioId,
            portfolio_value: List[DailyValue],
            start_date: Optional[str]=None
    ) -> PortfolioPerformance:
        """
        Calculate portfolio performance using TWR method.

        Optimized version that:
        1. Performs single TWR calculation instead of multiple redundant calculations
        2. Derives period-specific returns from cumulative returns
        3. Simplifies date grouping logic

        Args:
            portfolio_value: List of dictionaries containing daily portfolio values
            start_date: Optional start date for calculations (default: earliest date)

        Returns:
            PortfolioPerformance with TWR data for different time periods
        """
        # Prepare data once
        deposits, cash_flows, market_value_per_day = self._prepare_performance_data(selected_portfolio, portfolio_value)

        if not start_date:
            start_date = min(market_value_per_day.keys())
        end_date = max(max(cash_flows.keys(), default=start_date), max(market_value_per_day.keys()))

        # Single TWR calculation for entire period
        all_dates = self._get_business_date_range(start_date, end_date)
        main_twr = self._calculate_twr(all_dates, market_value_per_day, cash_flows)

        # Derive period-specific returns from cumulative returns
        annual_twr, monthly_twr = self._derive_period_returns(main_twr.cumulative_returns)

        # Format cumulative returns for frontend
        twr_series = [
            DailyValue(x=LocalizationUtility.format_date_from_date(date), y=return_value)
            for date, return_value in main_twr.cumulative_returns.items()
        ]

        return PortfolioPerformance(
            twr=twr_series,
            annual_twr=annual_twr,
            monthly_twr=monthly_twr
        )

    def _prepare_performance_data(self, selected_portfolio: PortfolioId, portfolio_value: List[DailyValue]):
        """Prepare and cache data needed for performance calculations."""
        # Cache deposits to avoid multiple retrievals (fixes FIXME)
        cache_key = f'_cached_deposits_{selected_portfolio.value}'
        if not hasattr(self, cache_key):
            deposits = sorted(
                self.deposits.get_cash_deposits(selected_portfolio),
                key=lambda k: k.datetime
            )
            setattr(self, cache_key, deposits)
        else:
            deposits = getattr(self, cache_key)

        # Convert deposits to cash flows
        cash_flows = defaultdict(float)
        for item in deposits:
            cash_flows[item.datetime_as_date()] += item.change

        # Convert portfolio values to dict
        market_value_per_day = {item['x']: item['y'] for item in portfolio_value}

        # Apply timing correction
        cash_flows = self._correct_cash_flow_timing(cash_flows, market_value_per_day)

        return deposits, cash_flows, market_value_per_day

    @staticmethod
    def _get_business_date_range(start_date: str, end_date: str) -> list[str]:
        """Generate business day range without pandas overhead."""
        date_range = pd.date_range(start=start_date, end=end_date, freq="B")
        return [date.strftime('%Y-%m-%d') for date in date_range]

    def _derive_period_returns(self, cumulative_returns: dict[datetime, float]) -> tuple[dict, dict]:
        """
        Derive annual and monthly returns from cumulative returns.
        Much more efficient than recalculating TWR for each period.
        """
        annual_twr = {}
        monthly_twr = defaultdict(self.__default_monthly_values)

        # Group returns by year and month
        returns_by_year = defaultdict(list)
        returns_by_month = defaultdict(list)

        for date, cum_return in cumulative_returns.items():
            year = str(date.year)
            month_name = LocalizationUtility.month_name(f"{date.month:02d}")

            returns_by_year[year].append((date, cum_return))
            returns_by_month[(year, month_name)].append((date, cum_return))

        # Calculate annual returns (from first to last day of each year)
        for year, year_returns in returns_by_year.items():
            if len(year_returns) >= 2:
                year_returns.sort(key=lambda x: x[0])
                start_return = year_returns[0][1]
                end_return = year_returns[-1][1]
                # Convert from cumulative returns to period return
                annual_twr[year] = (1 + end_return) / (1 + start_return) - 1

        # Calculate monthly returns (from first to last day of each month)
        for (year, month_name), month_returns in returns_by_month.items():
            if len(month_returns) >= 2:
                month_returns.sort(key=lambda x: x[0])
                start_return = month_returns[0][1]
                end_return = month_returns[-1][1]
                # Convert from cumulative returns to period return
                monthly_twr[year][month_name] = (1 + end_return) / (1 + start_return) - 1

        # Sort and convert to final format
        annual_twr = dict(sorted(annual_twr.items(), key=lambda x: x[0], reverse=True))
        monthly_twr = dict(sorted(
            {year: dict(months) for year, months in monthly_twr.items()}.items(),
            key=lambda x: x[0], reverse=True
        ))

        return annual_twr, monthly_twr

    def _correct_cash_flow_timing(self, cash_flows: dict, market_value_per_day: dict) -> dict:
        """
        Correct timing misalignment between when deposits appear in portfolio values
        vs. when they're officially recorded.

        This detects cases where:
        1. Portfolio value has a large jump on day X with no recorded cash flow
        2. A cash flow is recorded on day X+1 that roughly matches the jump
        3. Moves the cash flow from day X+1 to day X
        """
        corrected_cash_flows = cash_flows.copy()

        # Get all dates with portfolio values, sorted
        portfolio_dates = sorted(market_value_per_day.keys())

        # Track corrections made
        corrections_made = []

        for i in range(len(portfolio_dates) - 1):
            current_date = portfolio_dates[i]
            next_date = portfolio_dates[i + 1]

            current_value = market_value_per_day[current_date]
            next_value = market_value_per_day[next_date]

            # Skip if values are too small to be meaningful
            if current_value < 1000 or next_value < 1000:
                continue

            # Calculate day-over-day change
            day_change = next_value - current_value
            day_change_pct = abs(day_change / current_value)

            # Look for large changes (>20%) with no corresponding cash flow
            if day_change_pct > 0.20 and corrected_cash_flows.get(next_date, 0) == 0:

                # Look for a matching cash flow in the next few days
                for look_ahead in range(1, 4):  # Check next 1-3 days
                    if i + 1 + look_ahead >= len(portfolio_dates):
                        break

                    candidate_date = portfolio_dates[i + 1 + look_ahead]
                    candidate_cash_flow = corrected_cash_flows.get(candidate_date, 0)

                    if candidate_cash_flow != 0:
                        # Check if the cash flow roughly matches the portfolio jump
                        # Allow for some difference due to market movement
                        expected_jump = abs(candidate_cash_flow)
                        actual_jump = abs(day_change)

                        # If the cash flow is within 50% of the portfolio jump, it's likely a timing issue
                        if 0.5 <= actual_jump / expected_jump <= 1.5:
                            # Move the cash flow to the date when it actually affected portfolio
                            corrected_cash_flows[next_date] = candidate_cash_flow
                            corrected_cash_flows[candidate_date] = 0

                            corrections_made.append({
                                'from_date': candidate_date,
                                'to_date': next_date,
                                'amount': candidate_cash_flow,
                                'portfolio_jump': day_change,
                                'jump_pct': day_change_pct * 100
                            })

                            self.logger.info(f"Cash flow timing corrected: €{candidate_cash_flow:,.0f} moved "
                                             f"from {candidate_date} to {next_date} "
                                             f"(aligned with {day_change_pct*100:.1f}% portfolio change)")
                            break

        if corrections_made:
            self.logger.info(f"Applied {len(corrections_made)} cash flow timing corrections")

        return corrected_cash_flows


