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
from stonks_overwatch.services.models import DailyValue, PortfolioId
from stonks_overwatch.services.portfolio_aggregator import PortfolioAggregatorService
from stonks_overwatch.services.session_manager import SessionManager
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

    VALID_INTERVALS = frozenset({"YTD", "MTD", "1D", "1W", "1M", "3M", "6M", "1Y", "3Y", "5Y", "ALL"})
    VALID_VIEWS = frozenset({"performance", "value"})

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

        Args:
            portfolio_value: List of dictionaries containing daily portfolio values
            start_date: Optional start date for calculations (default: earliest date)

        Returns:
            List of dictionaries containing dates and cumulative returns
        """
        #FIXME: Can we avoid retrieving the deposits twice?
        deposits = sorted(
            self.deposits.get_cash_deposits(selected_portfolio),
            key=lambda k: k.datetime
        )

        cash_flows = defaultdict(float)
        for item in deposits:
            cash_flows[item.datetime_as_date()] += item.change

        market_value_per_day = { item['x']: item['y'] for item in portfolio_value }

        if not start_date:
            start_date = list(market_value_per_day.keys())[0]
        end_date = max(list(cash_flows.keys())[-1], list(market_value_per_day.keys())[-1])

        all_times_date_range, years_dict, month_years_dict = self.__group_date_range(start_date, end_date)

        annual_twr = {}
        monthly_twr = defaultdict(self.__default_monthly_values)
        all_times_twr = self.__get_date_range_performance_twr(all_times_date_range, market_value_per_day, cash_flows)
        for year in years_dict:
            annual_twr[year] = self.__get_total_performance_twr(years_dict[year], market_value_per_day, cash_flows)
        for year_month in month_years_dict:
            year, month = year_month.split("-")
            month_name = LocalizationUtility.month_name(month)
            date_range = month_years_dict[year_month]
            if len(date_range) == 1:
                # FIXME: The first day of the month this logic breaks
                continue
            monthly_twr[year][month_name] = self.__get_total_performance_twr(
                date_range=date_range,
                market_value_per_day=market_value_per_day,
                cash_flows=cash_flows
            )

        annual_twr = dict(sorted(annual_twr.items(), key=lambda entry: entry[0], reverse=True))
        monthly_twr = dict(sorted(monthly_twr.items(), key=lambda entry: entry[0], reverse=True))
        return PortfolioPerformance(
            twr=all_times_twr,
            annual_twr=annual_twr,
            monthly_twr={year: dict(months) for year, months in monthly_twr.items()}
        )

    def __get_date_range_performance_twr(
            self, date_range: list[str], market_value_per_day: dict[str, float], cash_flows: dict[str, float]
    ) -> List[Dict[str, float]]:
        twr = self._calculate_twr(date_range, market_value_per_day, cash_flows)

        return [
            DailyValue(x=LocalizationUtility.format_date_from_date(k), y=v)
            for k, v in twr.cumulative_returns.items()
        ]

    def __get_total_performance_twr(
            self, date_range: list[str], market_value_per_day: dict[str, float], cash_flows: dict[str, float]
    ) -> float:
        twr = self._calculate_twr(date_range, market_value_per_day, cash_flows)

        return twr.total_return

    @staticmethod
    def __group_date_range(start_date: str, end_date: str):
        """
        Groups dates in a range by year and month-year using Pandas.

        Args:
            start_date (date/datetime): Start date of the range
            end_date (date/datetime): End date of the range

        Returns:
            tuple: (all_dates_list, years_dict, month_years_dict) where:
                - all_dates_list: List of all the dates as values
                - years_dict: Dictionary with years as keys and lists of dates as values
                - month_years_dict: Dictionary with month-years as keys and lists of dates as values
        """
        # Create a date range using pandas
        date_range = pd.date_range(
            start=start_date,
            end=end_date,
            freq="B"  # Business days (excludes weekends)
        )

        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame({'date': date_range})

        # Add year and month-year columns
        df['year'] = df['date'].dt.year
        df['month_year'] = df['date'].dt.strftime('%Y-%m')

        # All dates
        all_dates_list = df['date'].dt.strftime('%Y-%m-%d').tolist()

        # Group by year
        years_dict = (df.groupby('year')['date']
                      .apply(lambda dates: [date.strftime('%Y-%m-%d') for date in dates])
                      .to_dict())

        # Group by month-year
        month_years_dict = (df.groupby('month_year')['date']
                            .apply(lambda dates: [date.strftime('%Y-%m-%d') for date in dates])
                            .to_dict())

        return all_dates_list, years_dict, month_years_dict
