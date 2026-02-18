import calendar
from datetime import date, datetime, timezone as dt_timezone
from typing import Optional

from currency_symbols import CurrencySymbols
from dateutil import parser as dateutil_parser


class LocalizationUtility:
    """
    A utility class for handling localization-related tasks, such as formatting dates, times, and currency values.

    This implementation uses python-dateutil to allow flexible parsing of incoming
    date/time strings (ISO, with or without timezone, or many other human formats).
    """

    TIME_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"
    MONTH_YEAR_FORMAT = "%B %Y"

    @staticmethod
    def _to_datetime(value: str | date | datetime) -> datetime:
        """Normalize input into a datetime instance.

        - If value is a datetime, return it as-is.
        - If value is a date (but not datetime), return a datetime at 00:00:00.
        - If value is a string, use dateutil.parser.parse for flexible parsing.
        """
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime(value.year, value.month, value.day, tzinfo=dt_timezone.utc)
        if isinstance(value, str):
            return dateutil_parser.parse(value)
        raise TypeError(f"Unsupported type: {type(value)}. Expected str, date or datetime.")

    @staticmethod
    def get_currency_symbol(currency: str) -> str:
        """
        Returns the currency symbol for the user's base currency.
        """
        base_currency_symbol = CurrencySymbols.get_symbol(currency)

        return base_currency_symbol

    @staticmethod
    def round_value(value: float) -> float:
        """
        Rounds a float value to 3 decimal places.
        """
        return round(value, 3)

    @staticmethod
    def format_money_value(value: float, currency: Optional[str] = None, currency_symbol: Optional[str] = None) -> str:
        """
        Formats a numeric value as a currency string with the specified currency symbol.
        If no currency symbol is provided, it uses the base currency symbol.
        """
        if not currency and not currency_symbol:
            raise ValueError("It's mandatory to provide a currency symbol or currency value.")

        if not currency_symbol:
            currency_symbol = CurrencySymbols.get_symbol(currency)

        if not isinstance(value, float):
            value = float(value)

        return f"{currency_symbol} {value:,.2f}"

    @staticmethod
    def format_date_time(value: str | date | datetime) -> str:
        """
        Formats a date and time value into 'YYYY-MM-DD HH:MM:SS'.
        Accepts a str, date or datetime. Strings are parsed with dateutil.
        """
        dt = LocalizationUtility._to_datetime(value)
        return dt.strftime(f"{LocalizationUtility.DATE_FORMAT} {LocalizationUtility.TIME_FORMAT}")

    @staticmethod
    def format_date(value: str | date | datetime) -> str:
        """
        Formats a date/time value to a date string 'YYYY-MM-DD'.
        """
        dt = LocalizationUtility._to_datetime(value)
        return dt.strftime(LocalizationUtility.DATE_FORMAT)

    @staticmethod
    def format_time(value: str | date | datetime) -> str:
        """
        Formats a date/time value to a time string 'HH:MM:SS'.
        """
        dt = LocalizationUtility._to_datetime(value)
        return dt.strftime(LocalizationUtility.TIME_FORMAT)

    @staticmethod
    def format_date_from_date(value: date) -> str:
        """
        Formats a datetime.date object to a date string.
        """
        return value.strftime(LocalizationUtility.DATE_FORMAT)

    @staticmethod
    def format_date_time_from_date(value: date | datetime) -> str:
        """
        Formats a datetime or date object to a datetime string.
        """
        dt = LocalizationUtility._to_datetime(value)
        return dt.strftime(f"{LocalizationUtility.DATE_FORMAT} {LocalizationUtility.TIME_FORMAT}")

    @staticmethod
    def format_time_from_date(value: datetime) -> str:
        """
        Formats a datetime object to a time string.
        """
        return value.strftime(LocalizationUtility.TIME_FORMAT)

    @staticmethod
    def format_date_to_month_year(value: str | date | datetime) -> str:
        """
        Formats a date value to a month and year string like 'January 2020'.
        """
        dt = LocalizationUtility._to_datetime(value)
        return dt.strftime(LocalizationUtility.MONTH_YEAR_FORMAT)

    @staticmethod
    def get_date_day(value: str | date | datetime) -> str:
        """
        Returns the day of the month from a date value (zero-padded string).
        """
        dt = LocalizationUtility._to_datetime(value)
        return dt.strftime("%d")

    @staticmethod
    def format_date_to_month_number(value: str | date | datetime) -> str:
        """
        Formats a date value to a month number string (zero-padded).
        """
        dt = LocalizationUtility._to_datetime(value)
        return dt.strftime("%m")

    @staticmethod
    def format_date_to_year(value: str | date | datetime) -> str:
        """
        Formats a date value to a year string.
        """
        dt = LocalizationUtility._to_datetime(value)
        return dt.strftime("%Y")

    @staticmethod
    def convert_string_to_date(value: str) -> date:
        """
        Converts a string to a date object using dateutil parsing.
        """
        return dateutil_parser.parse(value).date()

    @staticmethod
    def convert_string_to_datetime(value: str) -> datetime:
        """
        Converts a string to a datetime object using dateutil parsing.
        """
        return dateutil_parser.parse(value)

    @staticmethod
    def month_name(month_number: str | int) -> str:
        """Return the full month name for a given month number (1-12)."""
        num = int(month_number)
        if not 1 <= num <= 12:
            raise ValueError("month_number must be in 1..12")
        return calendar.month_name[num]

    @staticmethod
    def ensure_aware(value: str | date | datetime) -> datetime:
        """
        Normalizes a value into a timezone-aware datetime.
        Handles strings, date objects, and naive/aware datetime objects.
        """
        from django.utils import timezone

        dt = LocalizationUtility._to_datetime(value)
        if dt.tzinfo is None:
            return timezone.make_aware(dt)
        return dt

    @staticmethod
    def now() -> datetime:
        return datetime.now(dt_timezone.utc)
