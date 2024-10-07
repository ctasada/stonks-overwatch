import logging
from datetime import datetime

import pandas as pd
from currency_converter import CurrencyConverter
from django.shortcuts import render
from django.views import View

from degiro.services.account_overview import AccountOverviewService
from degiro.services.degiro_service import DeGiroService
from degiro.services.dividends import DividendsService
from degiro.utils.localization import LocalizationUtility


class Dividends(View):
    logger = logging.getLogger("stocks_portfolio.dividends.views")
    currency_converter = CurrencyConverter(fallback_on_missing_rate=True, fallback_on_wrong_date=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.degiro_service = DeGiroService()

        self.account_overview = AccountOverviewService()
        self.dividends = DividendsService(
            account_overview=self.account_overview,
            degiro_service=self.degiro_service,
        )
        self.base_currency = LocalizationUtility.get_base_currency()

    def get(self, request):
        dividends_overview = self.dividends.get_dividends()
        upcoming_dividends = self.dividends.get_upcoming_dividends()

        dividends_calendar = self._get_dividends_calendar(dividends_overview, upcoming_dividends)
        dividends_growth = self._get_dividends_growth(dividends_calendar)
        dividends_diversification = self._get_diversification(dividends_overview)
        total_dividends = self._get_total_dividends(dividends_calendar)

        context = {
            "total_dividends": total_dividends,
            "dividendsCalendar": dividends_calendar,
            "dividendsDiversification": dividends_diversification,
            "dividendsGrowth": dividends_growth,
            "currencySymbol": LocalizationUtility.get_base_currency_symbol(),
        }

        return render(request, "dividends.html", context)

    def _get_dividends_calendar(self, dividends_overview: list, upcoming_dividends: list):
        dividends_calendar = {}
        joined_dividends = dividends_overview + upcoming_dividends
        # After merging dividends and upcoming dividends, we need to sort the result
        joined_dividends = sorted(joined_dividends, key=lambda x: x["date"], reverse=True)

        df = pd.DataFrame(joined_dividends)
        period_start = min(df["date"])
        # Find the maximum date. Since we have upcoming payments, it can be today or some point
        # in the future
        date_as_datetime = pd.to_datetime(df["date"], format="%Y-%m-%d")
        today = pd.Timestamp("today").normalize()
        period_end = max(date_as_datetime.max(), today)
        period = pd.period_range(start=period_start, end=period_end, freq="M")[::-1]

        for month in period:
            month = month.strftime("%B %Y")
            month_entry = dividends_calendar.setdefault(month, {})
            month_entry.setdefault("payouts", 0)
            month_entry.setdefault("total", 0)
            month_entry.setdefault(
                "formatedTotal",
                LocalizationUtility.format_money_value(
                    value=0,
                    currency_symbol=LocalizationUtility.get_base_currency_symbol(),
                ),
            )

        for transaction in joined_dividends:
            # Group dividends by month. We may only need the dividend name and amount
            month_year = LocalizationUtility.format_date_to_month_year(transaction["date"])
            day = LocalizationUtility.get_date_day(transaction["date"])
            stock = transaction["stockSymbol"]

            month_entry = dividends_calendar.setdefault(month_year, {})
            days = month_entry.setdefault("days", {})
            day_entry = days.setdefault(day, {})
            stock_entry = day_entry.setdefault(stock, {})
            transaction_change = transaction["change"]

            currency = transaction["currency"]
            payment_date = LocalizationUtility.convert_string_to_date(transaction["date"])
            if currency != self.base_currency:
                transaction_change = self.currency_converter.convert(
                    transaction_change, currency, self.base_currency, payment_date
                )
                currency = self.base_currency

            stock_entry["stockName"] = transaction["stockName"]
            stock_entry["isUpcoming"] = payment_date > today.date()
            stock_entry["change"] = stock_entry.setdefault("change", 0) + transaction_change
            stock_entry["currency"] = currency
            stock_entry["formatedChange"] = LocalizationUtility.format_money_value(
                value=stock_entry["change"], currency=currency
            )

            month_entry.setdefault("dividends", []).append(
                {
                    "day": LocalizationUtility.get_date_day(transaction["date"]),
                    "stockName": transaction["stockName"],
                    "stockSymbol": transaction["stockSymbol"],
                    "formatedChange": transaction["formatedChange"],
                }
            )

            # Number of Payouts in the month
            payouts = month_entry.setdefault("payouts", 0)
            if transaction["change"] > 0:
                month_entry["payouts"] = payouts + 1
            # Total payout in the month
            total = month_entry.setdefault("total", 0)
            month_entry["total"] = total + transaction_change
            month_entry["formatedTotal"] = LocalizationUtility.format_money_value(
                value=month_entry["total"], currency=currency
            )

        return dividends_calendar

    def _get_dividends_growth(self, dividends_calendar: dict) -> dict:
        dividends_growth = {}

        for month_year in dividends_calendar.keys():
            month_number = int(datetime.strptime(month_year, "%B %Y").strftime("%m"))
            year = int(datetime.strptime(month_year, "%B %Y").strftime("%Y"))

            if year not in dividends_growth:
                dividends_growth[year] = [0] * 12

            month_entry = dividends_calendar.setdefault(month_year, {})

            dividends_growth[year][month_number - 1] = round(month_entry["total"], 2)

        # We want the Dividends Growth chronologically sorted
        dividends_growth = dict(sorted(dividends_growth.items(), key=lambda item: item[0]))
        return dividends_growth

    def _get_total_dividends(self, dividends_calendar: dict) -> str:
        total_dividends = 0
        for month_year in dividends_calendar.keys():
            month_entry = dividends_calendar.setdefault(month_year, {})
            total_dividends += month_entry["total"]

        return LocalizationUtility.format_money_value(value=total_dividends, currency=self.base_currency)

    def _get_diversification(self, dividends_overview: dict) -> dict:
        dividends_table = []
        dividends = {}

        total_dividends = 0
        max_percentage = 0.0

        for entry in dividends_overview:
            dividend_name = entry["stockName"]
            dividend_value = 0.0
            if dividend_name in dividends:
                dividend_value = dividends[dividend_name]["value"]

            dividend_currency = entry["currency"]
            dividend_change = entry["change"]
            if dividend_currency != self.base_currency:
                date = LocalizationUtility.convert_string_to_date(entry["date"])
                dividend_change = self.currency_converter.convert(
                    dividend_change, dividend_currency, self.base_currency, date
                )

            total_dividends += dividend_change
            dividends[dividend_name] = {
                "value": dividend_value + dividend_change,
            }

        # Calculate dividend ratios
        for key in dividends:
            dividends[key]["dividendsSize"] = dividends[key]["value"] / total_dividends
            max_percentage = max(max_percentage, dividends[key]["dividendsSize"])

        for key in dividends:
            dividends_size = dividends[key]["dividendsSize"]
            dividends_table.append(
                {
                    "name": key,
                    "value": dividends[key]["value"],
                    "size": dividends_size,
                    "formattedSize": f"{dividends_size:.2%}",
                    "weight": (dividends[key]["dividendsSize"] / max_percentage) * 100,
                }
            )
        dividends_table = sorted(dividends_table, key=lambda k: k["value"], reverse=True)

        dividends_labels = [row["name"] for row in dividends_table]
        dividends_values = [row["value"] for row in dividends_table]

        return {
            "chart": {
                "labels": dividends_labels,
                "values": dividends_values,
            },
            "table": dividends_table,
        }
