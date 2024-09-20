import logging
from collections import OrderedDict, defaultdict
from datetime import date, datetime, timedelta

import pandas as pd
from currency_converter import CurrencyConverter
from django.db import connection
from django.shortcuts import render
from django.views import View

from degiro.repositories.cash_movements_repository import CashMovementsRepository
from degiro.repositories.product_info_repository import ProductInfoRepository
from degiro.repositories.product_quotations_repository import ProductQuotationsRepository
from degiro.services.deposits import DepositsService
from degiro.services.dividends import DividendsService
from degiro.services.portfolio import PortfolioService
from degiro.utils.datetime import DateTimeUtility
from degiro.utils.db_utils import dictfetchall
from degiro.utils.localization import LocalizationUtility


class Dashboard(View):
    logger = logging.getLogger("stocks_portfolio.dashboard.views")
    currency_converter = CurrencyConverter(fallback_on_missing_rate=True, fallback_on_wrong_date=True)

    def __init__(self):
        self.deposits = DepositsService()
        self.dividends = DividendsService()
        self.portfolio_data = PortfolioService()
        self.product_quotations_repository = ProductQuotationsRepository()
        self.product_info_repository = ProductInfoRepository()
        self.cash_movements_repository = CashMovementsRepository()

    def get(self, request):
        total_costs = [{"x": item["date"], "y": item["total_cost"]} for item in self._total_costs_history()]
        cash_account = self.deposits.calculate_cash_account_value()
        portfolio_value = self._calculate_value(cash_account)
        cash_deposits_simple = self._get_simple_cash_deposits()
        performance_twr = self._calculate_performance_twr(cash_deposits_simple, portfolio_value)

        value_context = {
            "total_costs": total_costs,
            "portfolio_value": portfolio_value,
        }

        context = {
            "portfolio": {"value": value_context, "performance": performance_twr},
        }

        # FIXME: Simplify this response
        return render(request, "dashboard.html", context)

    def _get_simple_cash_deposits(self):
        result = {}

        for item in self.deposits.get_cash_deposits():
            date = item["date"]
            change = item["change"]

            if date in result:
                result[date] += change
            else:
                result[date] = change

        sorted_result = OrderedDict(sorted(result.items()))

        return sorted_result

    def _get_dividend_deposits(self) -> list:
        # {'date': '2020-05-15', 'currency': 'USD', 'change': 8.2, 'formatedChange': '$ 8.20']
        dividends = []
        base_currency = LocalizationUtility.get_base_currency()
        for dividend in self.dividends.get_dividends():
            dividend_date = LocalizationUtility.convert_string_to_date(dividend["date"])
            dividends.append(
                {
                    "date": dividend_date,
                    "change": self.currency_converter.convert(
                        dividend["change"], dividend["currency"], base_currency, dividend_date
                    ),
                }
            )

        return dividends

    def _total_costs_history(self) -> dict:
        cash_contributions = self.cash_movements_repository.get_cash_deposits_raw()
        dividends = self._get_dividend_deposits()

        df = pd.DataFrame.from_dict(cash_contributions + dividends)
        # Remove hours and keep only the day
        df["date"] = pd.to_datetime(df["date"]).dt.date
        # Group by day, adding the values
        df.set_index("date", inplace=True)
        df = df.sort_values(by="date")
        df = df.groupby(df.index)["change"].sum().reset_index()
        # Do the cummulative sum
        df["contributed"] = df["change"].cumsum()

        cash_contributions = df.to_dict("records")
        for contribution in cash_contributions:
            contribution["date"] = contribution["date"].strftime(LocalizationUtility.DATE_FORMAT)

        dataset = []
        for contribution in cash_contributions:
            dataset.append(
                {
                    "date": contribution["date"],
                    "total_cost": LocalizationUtility.round_value(contribution["contributed"]),
                }
            )

        # Append today with the last value to draw the line properly
        dataset.append(
            {
                "date": LocalizationUtility.format_date_from_date(date.today()),
                "total_cost": LocalizationUtility.round_value(cash_contributions[-1]["contributed"]),
            }
        )

        return dataset

    # FIXME: The TWR calculation seems off
    def _calculate_performance_twr(self, cash_contributions: dict, portfolio_value: dict) -> dict:
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

    def _calculate_value(self, cash_account: dict) -> list:
        data = self._create_products_quotation()
        stock_splits = self._get_stock_splits()

        base_currency = LocalizationUtility.get_base_currency()
        aggregate = {}
        for key in data:
            entry = data[key]
            position_value_growth = self._calculate_position_growth(entry, stock_splits)
            convert_fx = entry["product"]["currency"] != base_currency
            for date_value in position_value_growth:
                aggregate_value = aggregate.get(date_value, 0)

                if convert_fx:
                    currency = entry["product"]["currency"]
                    fx_date = LocalizationUtility.convert_string_to_date(date_value)
                    value = self.currency_converter.convert(
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

        # difference between current and previous date
        delta = timedelta(days=1)
        # store the dates between two dates in a list
        dates = []
        while start_date <= final_date:
            # add current date to list by converting  it to iso format
            dates.append(start_date.strftime(LocalizationUtility.DATE_FORMAT))
            # increment start date by timedelta
            start_date += delta

        position_value = {}
        for date_change in entry["history"]:
            index = dates.index(date_change)
            for d in dates[index:]:
                position_value[d] = entry["history"][date_change]

        splitted_stock = False
        if entry["productId"] in stock_splits:
            splitted_stock = True

        if splitted_stock:
            stocks_multiplier = 1
            for split_date in reversed(stock_splits[entry["productId"]]):
                split_data = stock_splits[entry["productId"]][split_date]
                stocks_multiplier = stocks_multiplier * split_data["split_ratio"]
                for date_value in reversed(position_value):
                    if date_value < split_date:
                        position_value[date_value] = position_value[date_value] * stocks_multiplier

        aggregate = {}
        for date_quote in entry["quotation"]["quotes"]:
            aggregate[date_quote] = position_value[date_quote] * entry["quotation"]["quotes"][date_quote]

        return aggregate

    def _get_stock_splits(self) -> dict:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT date, product_id, buysell, quantity FROM degiro_transactions
                    WHERE transaction_type_id = '101'
                """
            )
            results = dictfetchall(cursor)

        # Dictionary to hold grouped data
        grouped_data = defaultdict(lambda: {"B": None, "S": None})
        # Grouping the data by date and productId
        for entry in results:
            date = entry["date"].strftime(LocalizationUtility.DATE_FORMAT)
            buysell = entry["buysell"]
            grouped_data[date][buysell] = entry

        splitted_stocks = {}
        for date, transactions in grouped_data.items():
            sell_quantity = abs(transactions["S"]["quantity"])
            buy_quantity = transactions["B"]["quantity"]
            ratio = buy_quantity / sell_quantity

            sell_product_id = transactions["S"]["productId"]
            buy_product_id = transactions["B"]["productId"]
            product_split = {
                "productId_sell": sell_product_id,
                "productId_buy": buy_product_id,
                "is_renamed": transactions["S"]["productId"] != transactions["B"]["productId"],
                "split_ratio": ratio,
            }
            if sell_product_id not in splitted_stocks:
                splitted_stocks[sell_product_id] = {}
            if buy_product_id not in splitted_stocks:
                splitted_stocks[buy_product_id] = {}

            splitted_stocks[sell_product_id][date] = product_split
            splitted_stocks[buy_product_id][date] = product_split

        return splitted_stocks

    def _create_products_quotation(self) -> dict:
        product_growth = self.portfolio_data.calculate_product_growth()

        delete_keys = []
        for key in product_growth.keys():
            # FIXME: the method returns a key-value object
            product = self.product_info_repository.get_products_info_raw([key])[key]

            # If the product is NOT tradable, we shouldn't consider it for Growth
            # The 'tradable' attribute identifies old Stocks, like the ones that are
            # renamed for some reason, and it's not good enough to identify stocks
            # that are provided as dividends, for example.
            if "Non tradeable" in product["name"]:
                delete_keys.append(key)
                continue

            product_growth[key]["productId"] = key
            product_growth[key]["product"] = {}
            product_growth[key]["product"]["name"] = product["name"]
            product_growth[key]["product"]["isin"] = product["isin"]
            product_growth[key]["product"]["symbol"] = product["symbol"]
            product_growth[key]["product"]["currency"] = product["currency"]
            product_growth[key]["product"]["vwdId"] = product["vwdId"]
            product_growth[key]["product"]["vwdIdSecondary"] = product["vwdIdSecondary"]

            # Calculate Quotation Range
            product_growth[key]["quotation"] = {}
            product_history_dates = list(product_growth[key]["history"].keys())
            start_date = product_history_dates[0]
            final_date = LocalizationUtility.format_date_from_date(datetime.today())
            tmp_last = product_history_dates[-1]
            if product_growth[key]["history"][tmp_last] == 0:
                final_date = tmp_last

            product_growth[key]["quotation"]["fromDate"] = start_date
            product_growth[key]["quotation"]["toDate"] = final_date
            # Interval should be from start_date, since the QuoteCast query doesn't support more granularity
            product_growth[key]["quotation"]["interval"] = DateTimeUtility.calculate_interval(start_date)

        # Delete the non-tradable products
        for key in delete_keys:
            del product_growth[key]

        # We need to use the productIds to get the daily quote for each product
        for key in product_growth.keys():
            quotes_dict = self.product_quotations_repository.get_product_quotations(key)

            product_growth[key]["quotation"]["quotes"] = quotes_dict

        return product_growth
