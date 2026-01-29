import calendar
from datetime import datetime
from typing import List

from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from stonks_overwatch.config.config import Config
from stonks_overwatch.core.service_types import ServiceType
from stonks_overwatch.services.aggregators.trading_journal_aggregator import TradingJournalAggregatorService
from stonks_overwatch.services.models import Trade
from stonks_overwatch.services.utilities.session_manager import SessionManager
from stonks_overwatch.utils.core.localization import LocalizationUtility
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.views.mixins import CapabilityRequiredMixin


class TradingJournal(CapabilityRequiredMixin, View):
    """
    View for displaying and managing trading journal entries.

    This view provides functionality to view, add, edit, and delete trading journal entries
    across all enabled brokers.
    """

    required_capability = ServiceType.TRADING_JOURNAL
    logger = StonksLogger.get_logger("stonks_overwatch.trading_journal.views", "[VIEW|TRADING_JOURNAL]")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.trading_journal_aggregator = TradingJournalAggregatorService()
        self.base_currency = Config.get_global().base_currency

    def get(self, request):
        """Handle GET requests for trading journal page."""
        selected_portfolio = SessionManager.get_selected_portfolio(request)
        self.logger.debug(f"Selected Portfolio: {selected_portfolio}")

        granularity = self._parse_request_granularity(request)
        calendar_year = self._parse_request_calendar_year(request)
        calendar_month = self._parse_request_calendar_month(request)

        # Get trading journal entries
        entries = self.trading_journal_aggregator.get_closed_trades(selected_portfolio)

        if not entries:
            return render(request, "trading_journal.html", {"tradesCalendar": {"years": [], "calendar": {}}})

        calendar_data = self._get_trades_calendar(entries)

        # Filter calendar based on granularity and selection
        if granularity == "year":
            filtered_calendar = self._filter_calendar_by_year(calendar_data["calendar"], calendar_year)
            month_grid = None
        else:
            filtered_calendar = self._filter_calendar_by_month(calendar_data["calendar"], calendar_year, calendar_month)
            month_grid = self._get_month_grid(calendar_year, calendar_month, filtered_calendar)

        total_period_profit = sum(month_data.get("total", 0) for month_data in filtered_calendar.values())
        total_original_period_profit = sum(
            month_data.get("original_total", 0) for month_data in filtered_calendar.values()
        )

        # We assume for now that if we have original total, they all share the same currency for the summary
        # We can detect the currency from the first month that has it
        original_currency = next(
            (m.get("original_currency") for m in filtered_calendar.values() if m.get("original_currency")), None
        )

        calendar_data["calendar"] = filtered_calendar

        # Calculate navigation boundaries
        trade_dates = [trade.datetime for trade in entries]
        min_trade_date = min(trade_dates)

        now = timezone.now()

        context = {
            "tradesCalendar": calendar_data,
            "monthGrid": month_grid,
            "granularity": granularity,
            "selectedYear": calendar_year,
            "selectedMonth": calendar_month,
            "selectedMonthName": LocalizationUtility.month_name(calendar_month),
            "totalPeriodProfit": LocalizationUtility.format_money_value(
                value=total_period_profit, currency=self.base_currency
            ),
            "totalOriginalPeriodProfit": LocalizationUtility.format_money_value(
                value=total_original_period_profit, currency=original_currency
            )
            if original_currency
            else None,
            "originalCurrency": original_currency,
            "availableYears": calendar_data["years"],
            "availableMonths": [(i, LocalizationUtility.month_name(i)) for i in range(1, 13)],
            "minYear": min_trade_date.year,
            "minMonth": min_trade_date.month,
            "maxYear": now.year,
            "maxMonth": now.month,
        }

        if request.headers.get("Accept") == "application/json" or request.GET.get("html_only"):
            return self._handle_json_request(request, context)
        else:
            return render(request, "trading_journal.html", context)

    def _parse_request_granularity(self, request) -> str:
        """Parse granularity from request query parameters."""
        return request.GET.get("granularity", "month")

    def _parse_request_calendar_year(self, request) -> int:
        """Parse calendar year from request query parameters."""
        calendar_year = request.GET.get("calendar_year", timezone.now().year)
        return int(calendar_year)

    def _parse_request_calendar_month(self, request) -> int:
        """Parse calendar month from request query parameters."""
        calendar_month = request.GET.get("calendar_month", timezone.now().month)
        return int(calendar_month)

    def _filter_calendar_by_year(self, calendar: dict, year: int) -> dict:
        """Filter calendar to only include entries for the specified year."""
        return {key: value for key, value in calendar.items() if key.endswith(str(year))}

    def _filter_calendar_by_month(self, calendar: dict, year: int, month: int) -> dict:
        """Filter calendar to only include entries for the specified month and year."""
        month_name = LocalizationUtility.month_name(month)
        target_key = f"{month_name} {year}"
        return {key: value for key, value in calendar.items() if key == target_key}

    def _get_month_grid(self, year: int, month: int, filtered_calendar: dict) -> list:
        """Generate a 2D grid (weeks x days) for a monthly calendar view."""
        cal = calendar.Calendar(firstweekday=0)  # 0 is Monday
        month_name = LocalizationUtility.month_name(month)
        target_key = f"{month_name} {year}"
        month_data = filtered_calendar.get(target_key, {})
        days_data = month_data.get("days", {})

        grid = []
        for week in cal.monthdayscalendar(year, month):
            week_days = []
            weekly_total = 0
            weekly_original_total = 0
            weekly_original_currency = None
            for day in week:
                if day == 0:
                    week_days.append(None)
                else:
                    day_info = days_data.get(
                        day,
                        {
                            "day": day,
                            "tps": 0,
                            "total": 0,
                            "formatedTotal": LocalizationUtility.format_money_value(
                                value=0, currency=self.base_currency
                            ),
                        },
                    )
                    day_info["day"] = day
                    weekly_total += day_info.get("total", 0)
                    weekly_original_total += day_info.get("original_total", 0)
                    if day_info.get("original_currency"):
                        weekly_original_currency = day_info["original_currency"]
                    week_days.append(day_info)

            grid.append(
                {
                    "days": week_days,
                    "weeklyTotal": weekly_total,
                    "formatedWeeklyTotal": LocalizationUtility.format_money_value(
                        value=weekly_total, currency=self.base_currency
                    ),
                    "weeklyOriginalTotal": weekly_original_total,
                    "formatedWeeklyOriginalTotal": LocalizationUtility.format_money_value(
                        value=weekly_original_total, currency=weekly_original_currency
                    )
                    if weekly_original_currency
                    else None,
                }
            )
        return grid

    def _handle_json_request(self, request, context):
        """Handle AJAX/JSON requests."""
        if request.GET.get("html_only"):
            return render(request, "trading_journal/calendar.html", context)
        return JsonResponse(context, safe=False)

    def _get_trades_calendar(self, trades: List[Trade]) -> dict:
        trades_calendar = {}

        if not trades:
            return {
                "years": [],
                "calendar": {},
            }

        period_dates, years = self._generate_monthly_periods(trades)

        for month_date in period_dates:
            month = month_date.strftime(LocalizationUtility.MONTH_YEAR_FORMAT)
            month_entry = trades_calendar.setdefault(month, {})
            month_entry.setdefault("tps", 0)
            month_entry.setdefault("total", 0)
            month_entry.setdefault(
                "formatedTotal",
                LocalizationUtility.format_money_value(
                    value=0,
                    currency_symbol=LocalizationUtility.get_currency_symbol(self.base_currency),
                ),
            )

        for trade in trades:
            month_entry = trades_calendar.setdefault(trade.month_year(), {})
            days = month_entry.setdefault("days", {})
            day_entry = days.setdefault(int(trade.day()), {})
            day_entry["tps"] = day_entry.setdefault("tps", 0) + 1
            day_entry["total"] = round(day_entry.setdefault("total", 0) + trade.profit, 2)
            day_entry["formatedTotal"] = LocalizationUtility.format_money_value(
                value=day_entry["total"], currency=trade.currency
            )

            # Aggregate original values if available
            day_entry["original_total"] = round(
                day_entry.setdefault("original_total", 0) + (trade.original_profit or 0), 2
            )
            if trade.original_currency:
                day_entry["original_currency"] = trade.original_currency
                day_entry["formatedOriginalTotal"] = LocalizationUtility.format_money_value(
                    value=day_entry["original_total"], currency=trade.original_currency
                )

            # Number of TPS in the month
            month_entry["tps"] = month_entry.setdefault("tps", 0) + 1

            # Total payout in the month
            month_entry["total"] = round(month_entry.setdefault("total", 0) + trade.profit, 2)
            month_entry["formatedTotal"] = LocalizationUtility.format_money_value(
                value=month_entry["total"], currency=trade.currency
            )

            # Aggregate original monthly values
            month_entry["original_total"] = round(
                month_entry.setdefault("original_total", 0) + (trade.original_profit or 0), 2
            )
            if trade.original_currency:
                month_entry["original_currency"] = trade.original_currency
                month_entry["formatedOriginalTotal"] = LocalizationUtility.format_money_value(
                    value=month_entry["original_total"], currency=trade.original_currency
                )

        return {
            "years": years,
            "calendar": trades_calendar,
        }

    def _generate_monthly_periods(self, trades: List[Trade]) -> tuple[list[datetime], list[int]]:
        """
        Generate monthly periods from trade dates.

        Args:
            trades: List of trades

        Returns:
            Tuple of (period_dates, years) where:
            - period_dates: List of datetime objects representing monthly periods
            - years: Sorted list of unique years in descending order
        """
        payment_dates = [trade.datetime for trade in trades]

        # Find min/max dates directly
        min_date = min(payment_dates)
        max_date = max(payment_dates)

        # Set period_start to January 1st of the minimum year in the data
        min_year = min_date.year
        period_start = timezone.now().replace(year=min_year, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
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
