import logging
from collections import OrderedDict, defaultdict
from datetime import datetime, timedelta

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
        cash_account = self.deposits.calculate_cash_account_value()
        portfolio_value = self._calculate_value(cash_account)
        cash_deposits = self._aggregate_cash_deposits()
        performance_twr = self._calculate_performance_twr(cash_deposits, portfolio_value)

        context = {
            "portfolio": {
                "value": {"portfolio_value": portfolio_value},
                "performance": performance_twr,
            },
        }

        return render(request, "dashboard.html", context)

    def _aggregate_cash_deposits(self) -> dict[str, float]:
        """Aggregate cash deposits by date."""
        deposits = self.deposits.get_cash_deposits()
        aggregated = defaultdict(float)
        for item in deposits:
            aggregated[item["date"]] += item["change"]
        return dict(OrderedDict(sorted(aggregated.items())))

    # FIXME: The TWR calculation seems off
    def _calculate_performance_twr(self, cash_contributions: dict, portfolio_value: list[dict]) -> list[dict]:
        """Calculate the Time Weight Ratio (TWR).

        Formula to calculate TWR = [(1+RPN) x (1+ RPN) x … - 1] x 100
            Where RPN= ((NAVF-CF)/NAVI ) -1
            RPN: Return for period N
            NAVF: Portfolio final value for the period
            NAVI: Portfolio initial value for the period
            CF: Cashflow
        """
        portfolio_value = {item["x"]: item["y"] for item in portfolio_value}

        start_date = min(list(cash_contributions)[0], list(portfolio_value)[0])
        end_date = max(list(cash_contributions)[-1], list(portfolio_value)[-1])

        dataset = []

        initial_value = 0
        end_value = 0
        product = 1
        cash_flow = 0
        for day in pd.date_range(start=start_date, end=end_date, freq="d"):
            day = day.strftime(LocalizationUtility.DATE_FORMAT)
            cash_flow = cash_contributions.get(day, 0)
            portfolio_day_value = portfolio_value.get(day, 0)
            end_value = portfolio_day_value

            if initial_value == 0:
                initial_value = cash_flow
                continue

            rate = (end_value - initial_value + (-1 * cash_flow)) / initial_value

            # TWR = [(1+RPN) x (1+RPN) x … – 1] x 100
            product = product * (1 + rate)
            performance = product - 1

            initial_value = end_value

            dataset.append({"x": day, "y": performance})

        return dataset

    def _calculate_value(self, cash_account: dict) -> list[dict]:
        data = self._create_products_quotation()
        stock_splits = self._get_stock_splits()

        base_currency = self.degiro_service.get_base_currency()
        aggregate = {}
        for key in data:
            entry = data[key]
            position_value_growth = self._calculate_position_growth(entry, stock_splits)
            if len(position_value_growth) > 0 and list(position_value_growth.keys())[-1] == '2024-12-01':
                print(f"{key}: {entry["product"]}")
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
