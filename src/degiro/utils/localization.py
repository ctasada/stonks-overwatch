from datetime import date, datetime

from currency_symbols import CurrencySymbols

from degiro.config.degiro_config import DegiroConfig


class LocalizationUtility(object):
    TIME_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"

    # Get user's base currency
    @staticmethod
    def get_base_currency_symbol() -> str:
        base_currency = LocalizationUtility.get_base_currency()
        base_currency_symbol = CurrencySymbols.get_symbol(base_currency)

        return base_currency_symbol

    @staticmethod
    def get_base_currency() -> str:
        degiro_config = DegiroConfig.default()
        return degiro_config.base_currency

    @staticmethod
    def round_value(value: float) -> float:
        return round(value, 3)

    @staticmethod
    def format_money_value(value: float, currency: str = None, currency_symbol: str = None) -> str:
        if currency and not currency_symbol:
            currency_symbol = CurrencySymbols.get_symbol(currency)

        return currency_symbol + " {:,.2f}".format(value)

    @staticmethod
    def format_date_time(value: str) -> str:
        time = datetime.strptime(value, LocalizationUtility.TIME_DATE_FORMAT)
        return time.strftime(LocalizationUtility.DATE_FORMAT + " " + LocalizationUtility.TIME_FORMAT)

    @staticmethod
    def format_date(value: str) -> str:
        time = datetime.strptime(value, LocalizationUtility.TIME_DATE_FORMAT)
        return time.strftime(LocalizationUtility.DATE_FORMAT)

    @staticmethod
    def format_time(value: str) -> str:
        time = datetime.strptime(value, LocalizationUtility.TIME_DATE_FORMAT)
        return time.strftime(LocalizationUtility.TIME_FORMAT)

    @staticmethod
    def format_date_from_date(value: datetime) -> str:
        return value.strftime(LocalizationUtility.DATE_FORMAT)

    @staticmethod
    def format_time_from_date(value: datetime) -> str:
        return value.strftime(LocalizationUtility.TIME_FORMAT)

    @staticmethod
    def format_date_to_month_year(value: str) -> str:
        time = datetime.strptime(value, LocalizationUtility.DATE_FORMAT)
        return time.strftime("%B %Y")

    @staticmethod
    def get_date_day(value: str) -> str:
        time = datetime.strptime(value, LocalizationUtility.DATE_FORMAT)
        return time.strftime("%d")

    @staticmethod
    def format_date_to_month_number(value: str) -> str:
        time = datetime.strptime(value, LocalizationUtility.DATE_FORMAT)
        return time.strftime("%m")

    @staticmethod
    def format_date_to_year(value: str) -> str:
        time = datetime.strptime(value, LocalizationUtility.DATE_FORMAT)
        return time.strftime("%Y")

    @staticmethod
    def convert_string_to_date(value: str) -> date:
        return datetime.strptime(value, LocalizationUtility.DATE_FORMAT).date()

    @staticmethod
    def convert_string_to_datetime(value: str) -> date:
        return datetime.strptime(value, LocalizationUtility.TIME_DATE_FORMAT)
