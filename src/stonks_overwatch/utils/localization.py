from datetime import date, datetime, timezone
from typing import Optional

from currency_symbols import CurrencySymbols


class LocalizationUtility:
    """
    A utility class for handling localization-related tasks, such as formatting dates, times, and currency values.
    """

    TIME_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"

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
    def format_date_time(value: str) -> str:
        """
        Formats a date and time string in the specified format.
        """
        time = datetime.fromisoformat(value)
        return time.strftime(f"{LocalizationUtility.DATE_FORMAT} {LocalizationUtility.TIME_FORMAT}")

    @staticmethod
    def format_date(value: str) -> str:
        """
        Formats a date time string to date string.
        """
        time = datetime.strptime(value, LocalizationUtility.TIME_DATE_FORMAT)
        return time.strftime(LocalizationUtility.DATE_FORMAT)

    @staticmethod
    def format_time(value: str) -> str:
        """
        Formats a date time string to time string.
        """
        time = datetime.strptime(value, LocalizationUtility.TIME_DATE_FORMAT)
        return time.strftime(LocalizationUtility.TIME_FORMAT)

    @staticmethod
    def format_date_from_date(value: date) -> str:
        """
        Formats a datetime object to a date string.
        """
        return value.strftime(LocalizationUtility.DATE_FORMAT)

    @staticmethod
    def format_date_time_from_date(value: date | datetime) -> str:
        """
        Formats a datetime object to a datetime string.
        """
        return value.strftime(f"{LocalizationUtility.DATE_FORMAT} {LocalizationUtility.TIME_FORMAT}")

    @staticmethod
    def format_time_from_date(value: datetime) -> str:
        """
        Formats a datetime object to a time string.
        """
        return value.strftime(LocalizationUtility.TIME_FORMAT)

    @staticmethod
    def format_date_to_month_year(value: str) -> str:
        """
        Formats a date string to a month and year string.
        """
        time = datetime.strptime(value, LocalizationUtility.DATE_FORMAT)
        return time.strftime("%B %Y")

    @staticmethod
    def get_date_day(value: str) -> str:
        """
        Returns the day of the month from a date string.
        """
        time = datetime.strptime(value, LocalizationUtility.DATE_FORMAT)
        return time.strftime("%d")

    @staticmethod
    def format_date_to_month_number(value: str) -> str:
        """
        Formats a date string to a month number string.
        """
        time = datetime.strptime(value, LocalizationUtility.DATE_FORMAT)
        return time.strftime("%m")

    @staticmethod
    def format_date_to_year(value: str) -> str:
        """
        Formats a date string to a year string.
        """
        time = datetime.strptime(value, LocalizationUtility.DATE_FORMAT)
        return time.strftime("%Y")

    @staticmethod
    def convert_string_to_date(value: str) -> date:
        """
        Converts a string to a date object.
        """
        return datetime.fromisoformat(value).date()

    @staticmethod
    def convert_string_to_datetime(value: str) -> datetime:
        """
        Converts a string to a datetime object.
        """
        return datetime.fromisoformat(value)

    @staticmethod
    def month_name(month_number: str|int) -> str:
        return datetime(datetime.now().year, int(month_number), 1).strftime("%B")

    @staticmethod
    def now() -> datetime:
        return datetime.now(timezone.utc)
