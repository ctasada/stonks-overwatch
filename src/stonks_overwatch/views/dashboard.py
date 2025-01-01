import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
from django.shortcuts import render
from django.views import View

from stonks_overwatch.config import Config
from stonks_overwatch.services.degiro.degiro_service import DeGiroService
from stonks_overwatch.services.degiro.deposits import DepositsService
from stonks_overwatch.services.degiro.portfolio import PortfolioService
from stonks_overwatch.utils.localization import LocalizationUtility


class Dashboard(View):
    logger = logging.getLogger("stocks_portfolio.dashboard.views")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.degiro_service = DeGiroService()

        self.degiro_deposits = DepositsService(
            degiro_service=self.degiro_service,
        )
        self.degiro_portfolio = PortfolioService(
            degiro_service=self.degiro_service,
        )

    def get(self, request):
        """Handle GET request for dashboard view."""
        portfolio_value = []
        if Config.default().is_degiro_enabled():
            portfolio_value += self.degiro_portfolio.calculate_historical_value()

        performance_twr = self._calculate_performance_twr(portfolio_value)

        context = {
            "portfolio": {
                "value": {"portfolio_value": portfolio_value},
                "performance": performance_twr,
            },
        }

        return render(request, "dashboard.html", context)

    def _calculate_twr(self, dates: List[str], values: List[float], cashflows: List[float]) -> dict:
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
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'cumulative_returns': cumulative_returns,
            'total_days': total_days,
            'total_cashflows': sum(cashflows)
        }

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
            self.degiro_deposits.get_cash_deposits(),
            key=lambda k: k["date"]
        )

        cash_flows = defaultdict(float)
        for item in deposits:
            cash_flows[item['date']] += item['change']

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
            {
                "x": LocalizationUtility.format_date_from_date(k),
                "y": v
            } for k, v in twr['cumulative_returns'].items()
        ]
