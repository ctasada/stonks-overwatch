import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
from django.shortcuts import render
from django.views import View

from stonks_overwatch.repositories.degiro.product_info_repository import ProductInfoRepository
from stonks_overwatch.repositories.degiro.product_quotations_repository import ProductQuotationsRepository
from stonks_overwatch.repositories.degiro.transactions_repository import TransactionsRepository
from stonks_overwatch.services.degiro.account_overview import AccountOverviewService
from stonks_overwatch.services.degiro.currency_converter_service import CurrencyConverterService
from stonks_overwatch.services.degiro.degiro_service import DeGiroService
from stonks_overwatch.services.degiro.deposits import DepositsService
from stonks_overwatch.services.degiro.dividends import DividendsService
from stonks_overwatch.services.degiro.portfolio import PortfolioService
from stonks_overwatch.utils.datetime import DateTimeUtility
from stonks_overwatch.utils.localization import LocalizationUtility


class Dashboard(View):
    logger = logging.getLogger("stocks_portfolio.dashboard.views")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.degiro_service = DeGiroService()

        self.account_overview = AccountOverviewService()
        self.currency_service = CurrencyConverterService()
        self.deposits = DepositsService(
            degiro_service=self.degiro_service,
        )
        self.dividends = DividendsService(
            account_overview=self.account_overview,
            degiro_service=self.degiro_service,
        )
        self.portfolio_data = PortfolioService(
            degiro_service=self.degiro_service,
        )

    def get(self, request):
        """Handle GET request for dashboard view."""
        cash_account = self.deposits.calculate_cash_account_value()
        portfolio_value = self._calculate_value(cash_account)
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
            self.deposits.get_cash_deposits(),
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

    def _calculate_value(self, cash_account: dict) -> list[dict]:
        data = self._create_products_quotation()
        stock_splits = self._get_stock_splits()

        base_currency = self.degiro_service.get_base_currency()
        aggregate = {}
        for key in data:
            entry = data[key]
            position_value_growth = self._calculate_position_growth(entry, stock_splits)
            convert_fx = entry["product"]["currency"] != base_currency
            for date_value in position_value_growth:
                if self._is_weekend(date_value):
                    # Skip weekends. Those days there's no activity
                    continue

                aggregate_value = aggregate.get(date_value, 0)

                if convert_fx:
                    currency = entry["product"]["currency"]
                    fx_date = LocalizationUtility.convert_string_to_date(date_value)
                    value = self.currency_service.convert(
                        position_value_growth[date_value], currency, base_currency, fx_date
                    )
                    aggregate_value += value
                else:
                    aggregate_value += position_value_growth[date_value]
                aggregate[date_value] = aggregate_value

        dataset = []
        for day in aggregate:
            # Merges the portfolio value with the cash value to get the full picture
            cash_value = 0.0
            if day in cash_account:
                cash_value = cash_account[day]
            else:
                cash_value = list(cash_account.values())[-1]

            day_value = aggregate[day] + cash_value
            dataset.append({"x": day, "y": LocalizationUtility.round_value(day_value)})

        return dataset

    def _get_growth_final_date(self, date_str: str):
        if date_str == 0:
            return LocalizationUtility.convert_string_to_date(date_str)
        else:
            return datetime.today().date()

    def _calculate_position_growth(self, entry: dict, stock_splits: dict) -> dict:
        product_history_dates = list(entry["history"].keys())

        start_date = LocalizationUtility.convert_string_to_date(product_history_dates[0])
        final_date = self._get_growth_final_date(product_history_dates[-1])

        # Generate a list of dates between start and final date
        dates = [(start_date + timedelta(days=i)).strftime(LocalizationUtility.DATE_FORMAT)
                 for i in range((final_date - start_date).days + 1)]

        position_value = {}
        for date_change in entry["history"]:
            index = dates.index(date_change)
            for d in dates[index:]:
                position_value[d] = entry["history"][date_change]

        if entry["productId"] in stock_splits:
            stocks_multiplier = 1
            for split_date in reversed(stock_splits[entry["productId"]]):
                split_data = stock_splits[entry["productId"]][split_date]
                stocks_multiplier = stocks_multiplier * split_data["split_ratio"]
                for date_value in reversed(position_value):
                    if date_value < split_date:
                        position_value[date_value] = position_value[date_value] * stocks_multiplier

        aggregate = {}
        if entry["quotation"]["quotes"]:
            for date_quote in entry["quotation"]["quotes"]:
                if date_quote in position_value:
                    aggregate[date_quote] = position_value[date_quote] * entry["quotation"]["quotes"][date_quote]
        else:
            self.logger.warning(f"No quotes found for '{entry['product']['symbol']}': productId {entry['productId']} ")

        return aggregate

    def _get_stock_splits(self) -> dict:
        """
        Retrieves and processes stock split transactions.
        """
        results = TransactionsRepository.get_stock_split_transactions()
        grouped_data = defaultdict(lambda: {"B": None, "S": None})

        for entry in results:
            day = entry["date"].strftime(LocalizationUtility.DATE_FORMAT)
            grouped_data[day][entry["buysell"]] = entry

        stock_splits = {}
        for day, transactions in grouped_data.items():
            if not all(transactions.values()):
                continue

            sell_quantity = abs(transactions["S"]["quantity"])
            buy_quantity = transactions["B"]["quantity"]
            split_ratio = buy_quantity / sell_quantity

            split_data = {
                "productId_sell": transactions["S"]["productId"],
                "productId_buy": transactions["B"]["productId"],
                "is_renamed": transactions["S"]["productId"] != transactions["B"]["productId"],
                "split_ratio": split_ratio,
            }

            stock_splits.setdefault(transactions["S"]["productId"], {})[day] = split_data
            stock_splits.setdefault(transactions["B"]["productId"], {})[day] = split_data

        return stock_splits

    def _create_products_quotation(self) -> dict:
        """
        Creates product quotations based on portfolio data and product information.
        """
        product_growth = self.portfolio_data.calculate_product_growth()
        tradable_products = {}

        for key, data in product_growth.items():
            product = ProductInfoRepository.get_product_info_from_id(key)

            # If the product is NOT tradable, we shouldn't consider it for Growth
            # The 'tradable' attribute identifies old Stocks, like the ones that are
            # renamed for some reason, and it's not good enough to identify stocks
            # that are provided as dividends, for example.
            if "Non tradeable" in product.get("name", ""):
                continue

            data["productId"] = key
            data["product"] = {
                "name": product["name"],
                "isin": product["isin"],
                "symbol": product["symbol"],
                "currency": product["currency"],
                "vwdId": product["vwdId"],
                "vwdIdSecondary": product["vwdIdSecondary"],
            }

            product_history_dates = list(data["history"].keys())
            data["quotation"] = {
                "fromDate": product_history_dates[0],
                "toDate": LocalizationUtility.format_date_from_date(datetime.today()),
                "interval": DateTimeUtility.calculate_interval(product_history_dates[0]),
                "quotes": ProductQuotationsRepository.get_product_quotations(key),
            }
            tradable_products[key] = data

        return tradable_products

    def _is_weekend(self, date_str: str):
        # Parse the date string into a datetime object
        day = datetime.strptime(date_str, '%Y-%m-%d')
        # Check if the day of the week is Saturday (5) or Sunday (6)
        return day.weekday() >= 5
