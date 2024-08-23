from django.views import View
from django.shortcuts import render
import datetime
import pandas as pd
import logging

from degiro.integration.account_overview import AccountOverviewData
from degiro.utils.localization import LocalizationUtility

from currency_converter import CurrencyConverter


class Dividends(View):

    logger = logging.getLogger("stocks_portfolio.dividends.views")
    currencyConverter = CurrencyConverter(
        fallback_on_missing_rate=True, fallback_on_wrong_date=True
    )
    # FIXME: Replace by common Localization Pattern
    DATE_FORMAT = "%Y-%m-%d"

    def __init__(self):
        self.accountOverview = AccountOverviewData()
        self.baseCurrency = LocalizationUtility.get_base_currency()

    def get(self, request):
        # We don't need to sort the dict, since it's already coming sorted in DESC date order
        dividendsOverview = self.accountOverview.get_dividends()

        dividends = self.get_dividends_calendar(dividendsOverview)
        dividendsGrowth = {}

        for transaction in dividendsOverview:
            # Group dividends by month. We may only need the dividend name and amount
            monthYear = self.format_date_to_month_year(transaction["date"])
            monthNumber = int(self.format_date_to_month_number(transaction["date"]))
            year = int(self.format_date_to_year(transaction["date"]))

            if year not in dividendsGrowth:
                dividendsGrowth[year] = [0] * 12

            day = self.get_date_day(transaction["date"])
            stock = transaction["stockSymbol"]

            monthEntry = dividends.setdefault(monthYear, dict())
            days = monthEntry.setdefault("days", dict())
            dayEntry = days.setdefault(day, dict())
            stockEntry = dayEntry.setdefault(stock, dict())
            transactionChange = transaction["change"]

            currency = transaction["currency"]
            if currency != self.baseCurrency:
                date = datetime.datetime.strptime(
                    transaction["date"], self.DATE_FORMAT
                ).date()
                transactionChange = self.currencyConverter.convert(
                    transactionChange, currency, self.baseCurrency, date
                )
                currency = self.baseCurrency

            stockEntry["stockName"] = transaction["stockName"]
            stockEntry["change"] = (
                stockEntry.setdefault("change", 0) + transactionChange
            )
            stockEntry["currency"] = currency
            stockEntry["formatedChange"] = LocalizationUtility.format_money_value(
                value=stockEntry["change"], currency=currency
            )

            monthEntry.setdefault("dividends", []).append(
                {
                    "day": self.get_date_day(transaction["date"]),
                    "stockName": transaction["stockName"],
                    "stockSymbol": transaction["stockSymbol"],
                    "formatedChange": transaction["formatedChange"],
                }
            )

            # Number of Payouts in the month
            payouts = monthEntry.setdefault("payouts", 0)
            if transaction["change"] > 0:
                monthEntry["payouts"] = payouts + 1
            # Total payout in the month
            total = monthEntry.setdefault("total", 0)
            monthEntry["total"] = total + transactionChange
            monthEntry["formatedTotal"] = LocalizationUtility.format_money_value(
                value=monthEntry["total"], currency=currency
            )

            dividendsGrowth[year][monthNumber - 1] = round(monthEntry["total"], 2)

        # We want the Dividends Growth chronologically sorted
        dividendsGrowth = dict(
            sorted(dividendsGrowth.items(), key=lambda item: item[0])
        )

        context = {"dividendsCalendar": dividends, "dividendsGrowth": dividendsGrowth}

        return render(request, "dividends.html", context)

    def get_dividends_calendar(self, dividendsOverview):
        dividends = dict()

        df = pd.DataFrame(dividendsOverview)
        periodStart = min(df["date"])
        periodEnd = datetime.date.today()
        period = pd.period_range(start=periodStart, end=periodEnd, freq="M")[::-1]

        for month in period:
            month = month.strftime("%B %Y")
            monthEntry = dividends.setdefault(month, dict())
            monthEntry.setdefault("payouts", 0)
            monthEntry.setdefault("total", 0)
            monthEntry.setdefault(
                "formatedTotal",
                LocalizationUtility.format_money_value(
                    value=0,
                    currencySymbol=LocalizationUtility.get_base_currency_symbol(),
                ),
            )
        return dividends

    # FIXME: Move methods to Localization class
    def format_date_to_month_year(self, value: str):
        time = datetime.datetime.strptime(value, self.DATE_FORMAT)
        return time.strftime("%B %Y")

    def get_date_day(self, value: str):
        time = datetime.datetime.strptime(value, self.DATE_FORMAT)
        return time.strftime("%d")

    def format_date_to_month_number(self, value: str):
        time = datetime.datetime.strptime(value, self.DATE_FORMAT)
        return time.strftime("%m")

    def format_date_to_year(self, value: str):
        time = datetime.datetime.strptime(value, self.DATE_FORMAT)
        return time.strftime("%Y")
