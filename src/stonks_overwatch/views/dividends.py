from datetime import datetime
from typing import List

from django.shortcuts import render
from django.views import View

from stonks_overwatch.config.config import Config
from stonks_overwatch.services.aggregators.dividends_aggregator import DividendsAggregatorService
from stonks_overwatch.services.brokers.degiro.client.constants import ProductType
from stonks_overwatch.services.models import Dividend
from stonks_overwatch.services.utilities.session_manager import SessionManager
from stonks_overwatch.utils.core.localization import LocalizationUtility
from stonks_overwatch.utils.core.logger import StonksLogger


class Dividends(View):
    logger = StonksLogger.get_logger("stonks_overwatch.dividends.views", "[VIEW|DIVIDENDS]")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dividends = DividendsAggregatorService()
        self.base_currency = Config.get_global().base_currency

    def get(self, request):
        selected_portfolio = SessionManager.get_selected_portfolio(request)
        self.logger.debug(f"Selected Portfolio: {selected_portfolio}")

        calendar_year = self._parse_request_calendar_year(request)

        dividends_overview = self.dividends.get_dividends(selected_portfolio)

        dividends_calendar = self._get_dividends_calendar(dividends_overview)
        dividends_growth = self._get_dividends_growth(dividends_calendar["calendar"])
        dividends_diversification = self._get_diversification(dividends_overview)
        total_net_dividends = self._get_total_net_dividends(dividends_overview)
        total_gross_dividends = self._get_total_gross_dividends(dividends_overview)
        total_tax_dividends = total_net_dividends - total_gross_dividends

        if total_net_dividends > 0.0:
            # Filter the dividends_calendar to only include items matching the calendar_year
            filtered_calendar = {
                key: value for key, value in dividends_calendar["calendar"].items() if key.endswith(str(calendar_year))
            }
            dividends_calendar["calendar"] = filtered_calendar

            context = {
                "total_net_dividends": LocalizationUtility.format_money_value(
                    value=total_net_dividends, currency=self.base_currency
                ),
                "total_gross_dividends": LocalizationUtility.format_money_value(
                    value=total_gross_dividends, currency=self.base_currency
                ),
                "total_tax_dividends": LocalizationUtility.format_money_value(
                    value=total_tax_dividends, currency=self.base_currency
                ),
                "dividendsCalendar": dividends_calendar,
                "dividendsDiversification": dividends_diversification,
                "dividendsGrowth": dividends_growth,
                "currencySymbol": LocalizationUtility.get_currency_symbol(self.base_currency),
            }
        else:
            context = {}

        if request.headers.get("Accept") == "application/json" and request.GET.get("html_only"):
            # Return only the calendar HTML
            return render(request, "dividends/calendar.html", {"dividendsCalendar": dividends_calendar})

        return render(request, "dividends.html", context)

    def _parse_request_calendar_year(self, request) -> str:
        """Parse calendar year from request query parameters."""
        calendar_year = request.GET.get("calendar_year", datetime.now().year)

        return calendar_year

    def _get_dividends_calendar(self, dividends: List[Dividend]) -> dict:
        dividends_calendar = {}

        if not dividends:
            return {
                "years": [],
                "calendar": {},
            }

        period_dates, years = self._generate_monthly_periods(dividends)

        for month_date in period_dates:
            month = month_date.strftime(LocalizationUtility.MONTH_YEAR_FORMAT)
            month_entry = dividends_calendar.setdefault(month, {})
            month_entry.setdefault("payouts", 0)
            month_entry.setdefault("total", 0)
            month_entry.setdefault(
                "formatedTotal",
                LocalizationUtility.format_money_value(
                    value=0,
                    currency_symbol=LocalizationUtility.get_currency_symbol(self.base_currency),
                ),
            )

        for dividend_pay in dividends:
            month_entry = dividends_calendar.setdefault(dividend_pay.month_year(), {})
            days = month_entry.setdefault("days", {})
            day_entry = days.setdefault(dividend_pay.day(), {})

            if not day_entry.get(dividend_pay.stock_symbol):
                day_entry[dividend_pay.stock_symbol] = dividend_pay
            else:
                day_entry[dividend_pay.stock_symbol].amount += dividend_pay.amount
                day_entry[dividend_pay.stock_symbol].taxes += dividend_pay.taxes

            # Number of Payouts in the month
            payouts = month_entry.setdefault("payouts", 0)

            if dividend_pay.is_paid():
                if dividend_pay.amount > 0:
                    month_entry["payouts"] = payouts + 1
                # Total payout in the month
                month_entry["total"] = month_entry.setdefault("total", 0) + dividend_pay.net_amount()
                month_entry["formatedTotal"] = LocalizationUtility.format_money_value(
                    value=month_entry["total"], currency=dividend_pay.currency
                )

        return {
            "years": years,
            "calendar": dividends_calendar,
        }

    def _get_dividends_growth(self, dividends_calendar: dict) -> dict:
        dividends_growth = {}

        for month_year in dividends_calendar.keys():
            month_number = int(datetime.strptime(month_year, LocalizationUtility.MONTH_YEAR_FORMAT).strftime("%m"))
            year = int(datetime.strptime(month_year, LocalizationUtility.MONTH_YEAR_FORMAT).strftime("%Y"))

            if year not in dividends_growth:
                dividends_growth[year] = [0] * 12

            month_entry = dividends_calendar.setdefault(month_year, {})

            dividends_growth[year][month_number - 1] = round(month_entry["total"], 2)

        # We want the Dividend Growth chronologically sorted
        dividends_growth = dict(sorted(dividends_growth.items(), key=lambda item: item[0]))
        return dividends_growth

    def _get_total_net_dividends(self, dividends_list: List[Dividend]) -> float:
        total_net_dividends = 0
        for dividend in dividends_list:
            total_net_dividends += dividend.net_amount()

        return total_net_dividends

    def _get_total_gross_dividends(self, dividends_list: List[Dividend]) -> float:
        total_gross_dividends = 0
        for dividend in dividends_list:
            total_gross_dividends += dividend.gross_amount()

        return total_gross_dividends

    def _get_diversification(self, dividends_overview: List[Dividend]) -> dict:
        dividends_table = []
        dividends = {}

        total_dividends = 0
        max_percentage = 0.0

        for entry in dividends_overview:
            dividend_name = entry.formatted_name()
            dividend_value = 0.0
            if dividend_name in dividends:
                dividend_value = dividends[dividend_name]["value"]

            total_dividends += entry.net_amount()
            dividends[dividend_name] = {
                "value": dividend_value + entry.net_amount(),
                "symbol": entry.stock_symbol,
                "product_type": ProductType.STOCK.name,
            }

        # Calculate dividend ratios
        for key in dividends:
            dividends[key]["dividends_size"] = dividends[key]["value"] / total_dividends
            max_percentage = max(max_percentage, dividends[key]["dividends_size"])

        for key in dividends:
            dividends_size = dividends[key]["dividends_size"]
            dividends_table.append(
                {
                    "name": key,
                    "value": dividends[key]["value"],
                    "formatted_value": LocalizationUtility.format_money_value(
                        value=dividends[key]["value"], currency=self.base_currency
                    ),
                    "size": dividends_size,
                    "formatted_size": f"{dividends_size:.2%}",
                    "weight": (dividends[key]["dividends_size"] / max_percentage) * 100,
                    "symbol": dividends[key]["symbol"],
                    "product_type": dividends[key]["product_type"],
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

    def _generate_monthly_periods(self, dividends: List[Dividend]) -> tuple[list[datetime], list[int]]:
        """
        Generate monthly periods from dividend payment dates.

        Args:
            dividends: List of dividend objects

        Returns:
            Tuple of (period_dates, years) where:
            - period_dates: List of datetime objects representing monthly periods
            - years: Sorted list of unique years in descending order
        """
        payment_dates = [dividend.payment_date for dividend in dividends]

        # Find min/max dates directly
        min_date = min(payment_dates)
        max_date = max(payment_dates)

        # Set period_start to January 1st of the minimum year in the data
        min_year = min_date.year
        period_start = datetime(year=min_year, month=1, day=1)
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = max(max_date, today)

        # Generate monthly periods using simple date arithmetic
        period_dates = []
        current = period_start
        while current <= period_end:
            period_dates.append(current)
            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        # Extract unique years from the period
        years = sorted({date.year for date in period_dates}, reverse=True)

        return period_dates, years
