from degiro.config.degiro_config import DegiroConfig
from currency_symbols import CurrencySymbols
from datetime import datetime


class LocalizationUtility(object):
    TIME_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"

    # Get user's base currency
    @staticmethod
    def get_base_currency_symbol() -> str:
        baseCurrency = LocalizationUtility.get_base_currency()
        baseCurrencySymbol = CurrencySymbols.get_symbol(baseCurrency)

        return baseCurrencySymbol

    @staticmethod
    def get_base_currency() -> str:
        degiro_config = DegiroConfig.default()
        return degiro_config.base_currency

    @staticmethod
    def round_value(value: float) -> float:
        return round(value, 3)

    @staticmethod
    def format_money_value(
        value: float, currency: str = None, currencySymbol: str = None
    ) -> str:
        if currency and not currencySymbol:
            currencySymbol = CurrencySymbols.get_symbol(currency)

        return currencySymbol + " {:,.2f}".format(value)

    @staticmethod
    def format_date_time(value: str) -> str:
        time = datetime.strptime(value, LocalizationUtility.TIME_DATE_FORMAT)
        return time.strftime(LocalizationUtility.DATE_FORMAT
                             + " "
                             + LocalizationUtility.TIME_FORMAT)

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
