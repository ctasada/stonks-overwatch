from degiro.utils.degiro import DeGiro
from currency_symbols import CurrencySymbols
from datetime import datetime

class LocalizationUtility(object):
    TIME_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
    DATE_FORMAT = '%Y-%m-%d'

    # Get user's base currency
    @staticmethod
    def get_base_currency_symbol():
        baseCurrency = LocalizationUtility.get_base_currency()
        baseCurrencySymbol = CurrencySymbols.get_symbol(baseCurrency)

        return baseCurrencySymbol
    
    @staticmethod
    def get_base_currency():
        accountInfo = DeGiro.get_account_info()
        baseCurrency = accountInfo['data']['baseCurrency']

        return baseCurrency

    @staticmethod
    def round_value(value: float):
        return round(value, 3)

    @staticmethod
    def format_money_value(value: float, currency: str = None, currencySymbol : str = None):
        if (currency and not currencySymbol):
            currencySymbol = CurrencySymbols.get_symbol(currency)
        
        return currencySymbol + " {:,.2f}".format(value)

    @staticmethod
    def format_date_time(value: str):
        time = datetime.strptime(value, LocalizationUtility.TIME_DATE_FORMAT)
        return time.strftime('%Y-%m-%d %H:%M:%S')
    
    @staticmethod
    def convert_datetime_to_date(value: str):
        time = datetime.strptime(value, LocalizationUtility.TIME_DATE_FORMAT)
        return time.strftime(LocalizationUtility.DATE_FORMAT)