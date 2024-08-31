import datetime
import logging

import pandas as pd
from currency_converter import CurrencyConverter
from django.shortcuts import render
from django.views import View

from degiro.data.account_overview import AccountOverviewData
from degiro.utils.localization import LocalizationUtility


class Dividends(View):
    logger = logging.getLogger("stocks_portfolio.dividends.views")
    currency_converter = CurrencyConverter(fallback_on_missing_rate=True, fallback_on_wrong_date=True)

    def __init__(self):
        self.accountOverview = AccountOverviewData()
        self.baseCurrency = LocalizationUtility.get_base_currency()

    def get(self, request):
        # We don't need to sort the dict, since it's already coming sorted in DESC date order
        dividends_overview = self.accountOverview.get_dividends()

        dividends = self.get_dividends_calendar(dividends_overview)
        dividends_growth = {}

        for transaction in dividends_overview:
            # Group dividends by month. We may only need the dividend name and amount
            month_year = LocalizationUtility.format_date_to_month_year(transaction["date"])
            month_number = int(LocalizationUtility.format_date_to_month_number(transaction["date"]))
            year = int(LocalizationUtility.format_date_to_year(transaction["date"]))

            if year not in dividends_growth:
                dividends_growth[year] = [0] * 12

            day = LocalizationUtility.get_date_day(transaction["date"])
            stock = transaction["stockSymbol"]

            month_entry = dividends.setdefault(month_year, {})
            days = month_entry.setdefault("days", {})
            day_entry = days.setdefault(day, {})
            stock_entry = day_entry.setdefault(stock, {})
            transaction_change = transaction["change"]

            currency = transaction["currency"]
            if currency != self.baseCurrency:
                date = LocalizationUtility.convert_string_to_date(transaction["date"])
                transaction_change = self.currency_converter.convert(
                    transaction_change, currency, self.baseCurrency, date
                )
                currency = self.baseCurrency

            stock_entry["stockName"] = transaction["stockName"]
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

            dividends_growth[year][month_number - 1] = round(month_entry["total"], 2)

        # We want the Dividends Growth chronologically sorted
        dividends_growth = dict(sorted(dividends_growth.items(), key=lambda item: item[0]))

        context = {"dividendsCalendar": dividends, "dividendsGrowth": dividends_growth}

        return render(request, "dividends.html", context)

    def get_dividends_calendar(self, dividends_overview):
        dividends = {}

        df = pd.DataFrame(dividends_overview)
        period_start = min(df["date"])
        period_end = datetime.date.today()
        period = pd.period_range(start=period_start, end=period_end, freq="M")[::-1]

        for month in period:
            month = month.strftime("%B %Y")
            month_entry = dividends.setdefault(month, {})
            month_entry.setdefault("payouts", 0)
            month_entry.setdefault("total", 0)
            month_entry.setdefault(
                "formatedTotal",
                LocalizationUtility.format_money_value(
                    value=0,
                    currency_symbol=LocalizationUtility.get_base_currency_symbol(),
                ),
            )
        return dividends
