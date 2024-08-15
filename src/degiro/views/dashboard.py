from collections import defaultdict
from datetime import date, datetime, timedelta
from django.views import View
from django.shortcuts import render
from django.db import connection

import pandas as pd

from degiro.utils.db_utils import dictfetchall
from degiro.integration.portfolio import PortfolioData
from degiro.utils.localization import LocalizationUtility
from degiro_connector.quotecast.models.chart import Interval

from currency_converter import CurrencyConverter

import logging
import json


class Dashboard(View):
    logger = logging.getLogger("stocks_portfolio.dashboard.views")
    currencyConverter = CurrencyConverter(
        fallback_on_missing_rate=True, fallback_on_wrong_date=True
    )

    def __init__(self):
        self.portfolio = PortfolioData()

    def get(self, request):
        sectorsContext = self._getSectors()
        cash_contributions = self._calculate_cash_contributions()
        portfolio_value = self._calculate_value()
        performanceTWR = self._calculate_performance_twr(portfolio_value)

        valueContext = {
            "cash_contributions": cash_contributions,
            "portfolio_value": portfolio_value,
        }

        context = {
            "portfolio": {"value": valueContext, "performance": performanceTWR},
            "sectors": sectorsContext,
        }

        # self.logger.debug(context)

        # FIXME: Simplify this response
        return render(request, "dashboard.html", context)

    def _calculate_performance_twr(self, portfolio_value: dict):
        """
        Formula to calculate TWR = [(1+RPN) x (1+ RPN) x … – 1] x 100
        Where RPN= ((NAVF-CF)/NAVI ) -1
        RPN: Return for period N
        NAVF: Portfolio final value for the period
        NAVI: Portfolio initial value for the period
        CF: Cashflow
        """
        tmpData = self._calculate_cash_contributions()
        cash_contributions = {item["x"]: item["y"] for item in tmpData}
        portfolio_value = {item["x"]: item["y"] for item in portfolio_value}

        # print(cash_contributions)
        # {
        #  '2020-03-10': 10000.01, '2020-03-11': 5000.01, '2020-08-21': 10000.01,
        #  '2020-12-03': 20000.010000000002, '2021-02-10': 22000.010000000002,
        #  '2021-05-27': 25000.010000000002, '2021-06-24': 30000.010000000002,
        #  '2022-02-01': 35000.01, '2023-01-09': 49000.01, '2024-02-23': 54000.01,
        #  '2024-07-28': 54000.01
        # }

        start_date = next(iter(cash_contributions))
        end_date = date.today()

        dataset = []

        finalValue = None
        aggregated_twr = 1

        for day in pd.date_range(start=start_date, end=end_date, freq="d"):
            day = day.strftime(LocalizationUtility.DATE_FORMAT)

            cf = cash_contributions.get(day, 0)
            if finalValue is None:
                finalValue = cf
            initialValue = finalValue
            finalValue = portfolio_value.get(day, None)
            if finalValue is None:
                finalValue = initialValue

            if initialValue == 0:
                break

            rpn = (finalValue - initialValue) / initialValue

            # TWR = [(1+RPN) x (1+ RPN) x … – 1] x 100
            aggregated_twr = aggregated_twr * (1 + rpn)
            performance = aggregated_twr - 1

            # count += 1
            # if (count < 10 or math.isinf(performance)):
            #     print(f"{day}: {rpn} = (({finalValue} - {initialValue}) / {initialValue})")
            #     print(f"       {performance}")

            dataset.append({"x": day, "y": performance})

        return dataset

    def _getSectors(self):
        portfolio = self.portfolio.get_portfolio()
        portfolio = sorted(portfolio, key=lambda k: k["sector"])
        # self.logger.debug(json.dumps(portfolio, indent=2))

        sectors = {}

        stockLabels = []
        stockValues = []

        for stock in portfolio:
            if stock["isOpen"]:
                sectorName = stock["sector"]
                sectors[sectorName] = sectors.get(sectorName, 0) + stock["value"]
                stockLabels.append(stock["symbol"])
                stockValues.append(stock["value"])

        sectorLabels = []
        sectorValues = []
        for key in sectors:
            sectorLabels.append(key)
            sectorValues.append(sectors[key])

        return {
            "sectors": {
                "labels": sectorLabels,
                "values": sectorValues,
            },
            "stocks": {
                "labels": stockLabels,
                "values": stockValues,
            },
            "currencySymbol": LocalizationUtility.get_base_currency_symbol(),
        }

    def _calculate_cash_contributions(self) -> dict:
        # FIXME: DeGiro doesn't have a consistent description or type. Missing the new value for 'Refund'
        # Known types:
        # CASH_FUND_NAV_CHANGE
        # CASH_FUND_TRANSACTION
        # CASH_TRANSACTION
        # FLATEX_CASH_SWEEP
        # PAYMENT
        # TRANSACTION
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT date, description, change
                FROM degiro_cashmovements
                WHERE currency = 'EUR'
                    AND description IN ('iDEAL storting', 'iDEAL Deposit', 'Terugstorting')
                """
            )
            cashContributions = dictfetchall(cursor)

        df = pd.DataFrame.from_dict(cashContributions)
        # Remove hours and keep only the day
        df["date"] = pd.to_datetime(df["date"]).dt.date
        # Group by day, adding the values
        df.set_index("date", inplace=True)
        df = df.sort_values(by="date")
        df = df.groupby(df.index)["change"].sum().reset_index()
        # Do the cummulative sum
        df["contributed"] = df["change"].cumsum()

        cashContributions = df.to_dict("records")
        for contribution in cashContributions:
            contribution["date"] = contribution["date"].strftime("%Y-%m-%d")

        dataset = []
        for contribution in cashContributions:
            dataset.append(
                {
                    "x": contribution["date"],
                    "y": LocalizationUtility.round_value(contribution["contributed"]),
                }
            )

        # Append today with the last value to draw the line properly
        dataset.append(
            {
                "x": date.today().strftime("%Y-%m-%d"),
                "y": cashContributions[-1]["contributed"],
            }
        )

        return dataset

    def _calculate_cash_account_value(self) -> dict:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT date, balance_total
                FROM degiro_cashmovements
                WHERE currency = 'EUR'
                    AND type = 'CASH_TRANSACTION'
                """
            )
            cashContributions = dictfetchall(cursor)

        # Create DataFrame from the fetched data
        df = pd.DataFrame.from_dict(cashContributions)

        # Convert the 'date' column to datetime and remove the time component
        df["date"] = pd.to_datetime(df["date"]).dt.normalize()

        # Group by date and take the last balance_total for each day
        df = df.groupby("date", as_index=False).last()

        # Sort values by date (just in case)
        df = df.sort_values(by="date")

        # Set the 'date' column as the index and fill missing dates
        df.set_index("date", inplace=True)
        df = df.resample("D").ffill()

        # Convert the DataFrame to a dictionary with date as the key (converted to string) and balance_total as the value
        dataset = {
            date.strftime("%Y-%m-%d"): float(balance)
            for date, balance in df["balance_total"].items()
        }

        return dataset

    def _get_productInfo(self, productId: int) -> dict:
        """
        Gets product information from the given product id. The information is retrieved from the DB.
        ### Parameters
            * productId: int
                - The product id to query
        ### Returns
            list: list of product ids
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM degiro_productinfo WHERE id = %s
                """,
                [productId],
            )
            result = dictfetchall(cursor)[0]

        return result

    def _get_product_quotations(self, productId: int) -> dict:
        """
        Gets the list of product ids from the DB.

        ### Returns
            list: list of product ids
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT quotations FROM degiro_productquotation WHERE id = %s
                """,
                [productId],
            )
            # FIXME: Avoid this manual conversion
            results = dictfetchall(cursor)[0]["quotations"]

        return json.loads(results)

    def _calculate_value(self) -> list:
        data = self._create_products_quotation()
        stockSplits = self._get_stock_splits()

        baseCurrency = LocalizationUtility.get_base_currency()
        aggregate = dict()
        for key in data:
            entry = data[key]
            position_value_growth = self._calculate_position_growth(entry, stockSplits)
            convert_fx = entry["product"]["currency"] != baseCurrency
            for date_value in position_value_growth:
                aggregate_value = aggregate.get(date_value, 0)

                if convert_fx:
                    currency = entry["product"]["currency"]
                    fx_date = datetime.strptime(
                        date_value, LocalizationUtility.DATE_FORMAT
                    ).date()
                    value = self.currencyConverter.convert(
                        position_value_growth[date_value], currency, baseCurrency, fx_date
                    )
                    aggregate_value += value
                else:
                    aggregate_value += position_value_growth[date_value]
                aggregate[date_value] = aggregate_value

        cash_account = self._calculate_cash_account_value()

        dataset = []
        latest_day = None
        for day in aggregate:
            # Merges the portfolio value with the cash value to get the full picture
            cash_value = 0.0
            if day in cash_account:
                cash_value = cash_account[day]
                latest_day = day
            else:
                cash_value = cash_account[latest_day]

            day_value = aggregate[day] + cash_value
            dataset.append({"x": day, "y": LocalizationUtility.round_value(day_value)})

        return dataset

    def _calculate_position_growth(self, entry: dict, stockSplits: dict) -> dict:
        product_history_dates = list(entry["history"].keys())

        start_date = datetime.strptime(
            product_history_dates[0], LocalizationUtility.DATE_FORMAT
        ).date()
        if product_history_dates[-1] == 0:
            final_date = datetime.strptime(
                product_history_dates[-1], LocalizationUtility.DATE_FORMAT
            ).date()
        else:
            final_date = datetime.today().date()

        # difference between current and previous date
        delta = timedelta(days=1)
        # store the dates between two dates in a list
        dates = []
        while start_date <= final_date:
            # add current date to list by converting  it to iso format
            dates.append(start_date.strftime(LocalizationUtility.DATE_FORMAT))
            # increment start date by timedelta
            start_date += delta

        position_value = dict()
        for date_change in entry["history"]:
            index = dates.index(date_change)
            for d in dates[index:]:
                position_value[d] = entry["history"][date_change]

        splittedStock = False
        if entry["productId"] in stockSplits:
            splittedStock = True

        if splittedStock:
            stocksMultiplier = 1
            for splitDate in reversed(stockSplits[entry["productId"]]):
                splitData = stockSplits[entry["productId"]][splitDate]
                stocksMultiplier = stocksMultiplier * splitData["split_ratio"]
                for date_value in reversed(position_value):
                    if date_value < splitDate:
                        position_value[date_value] = position_value[date_value] * stocksMultiplier

        aggregate = dict()
        for date_quote in entry["quotation"]["quotes"]:
            aggregate[date_quote] = position_value[date_quote] * entry["quotation"]["quotes"][date_quote]

        return aggregate

    def _calculate_interval(self, date_from) -> Interval:
        """
        Calculates the interval between the provided date and today
        ### Parameters
            date_from: date from to calculate the interval
        ### Returns
            Interval: Interval that representes the range from date_from to today
        """
        # Convert String to date object
        d1 = datetime.strptime(date_from, LocalizationUtility.DATE_FORMAT)
        today = datetime.today()
        # difference between dates in timedelta
        delta = (today - d1).days

        interval = None
        match delta:
            case diff if diff in range(1, 7):
                interval = Interval.P1W
            case diff if diff in range(7, 30):
                interval = Interval.P1M
            case diff if diff in range(30, 90):
                interval = Interval.P3M
            case diff if diff in range(90, 180):
                interval = Interval.P6M
            case diff if diff in range(180, 365):
                interval = Interval.P1Y
            case diff if diff in range(365, 3 * 365):
                interval = Interval.P3Y
            case diff if diff in range(3 * 365, 5 * 365):
                interval = Interval.P5Y
            case diff if diff in range(5 * 365, 10 * 365):
                interval = Interval.P10Y

        return interval

    def _get_stock_splits(self) -> dict:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT date, productId, buysell, quantity FROM degiro_transactions
                    WHERE transactionTypeId = '101'
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

            sell_productId = transactions["S"]["productId"]
            buy_productId = transactions["B"]["productId"]
            productSplit = {
                "productId_sell": sell_productId,
                "productId_buy": buy_productId,
                "is_renamed": transactions["S"]["productId"]
                != transactions["B"]["productId"],
                "split_ratio": ratio,
            }
            if sell_productId not in splitted_stocks:
                splitted_stocks[sell_productId] = {}
            if buy_productId not in splitted_stocks:
                splitted_stocks[buy_productId] = {}

            splitted_stocks[sell_productId][date] = productSplit
            splitted_stocks[buy_productId][date] = productSplit

        return splitted_stocks

    def _create_products_quotation(self) -> dict:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT date, productId, quantity FROM degiro_transactions
                """
            )
            results = dictfetchall(cursor)

        product_growth = {}
        for entry in results:
            key = entry["productId"]
            product = product_growth.get(key, {})
            carry_total = product.get("carry_total", 0)

            stock_date = entry["date"].strftime(LocalizationUtility.DATE_FORMAT)
            carry_total += entry["quantity"]

            product["carry_total"] = carry_total
            if "history" not in product:
                product["history"] = {}
            product["history"][stock_date] = carry_total
            product_growth[key] = product

        delete_keys = []
        for key in product_growth.keys():
            # Cleanup 'carry_total' from result
            del product_growth[key]["carry_total"]
            product = self._get_productInfo(key)

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
            final_date = datetime.today().strftime(LocalizationUtility.DATE_FORMAT)
            tmp_last = product_history_dates[-1]
            if product_growth[key]["history"][tmp_last] == 0:
                final_date = tmp_last

            product_growth[key]["quotation"]["from_date"] = start_date
            product_growth[key]["quotation"]["to_date"] = final_date
            # Interval should be from start_date, since the QuoteCast query doesn't support more granularity
            product_growth[key]["quotation"]["interval"] = self._calculate_interval(
                start_date
            )

        # Delete the non-tradable products
        for key in delete_keys:
            del product_growth[key]

        # We need to use the productIds to get the daily quote for each product
        for key in product_growth.keys():
            quotes_dict = self._get_product_quotations(key)

            product_growth[key]["quotation"]["quotes"] = quotes_dict

        return product_growth
